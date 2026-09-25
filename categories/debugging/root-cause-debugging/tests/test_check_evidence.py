"""Tests for record validation, not claims about real-world diagnosis quality."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'check_evidence.py'
spec = importlib.util.spec_from_file_location('check_evidence', SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class EvidenceChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'case'
        shutil.copytree(ROOT / 'examples' / 'atomic-archive', self.root)
        self.record = json.loads((self.root / 'evidence.json').read_text(encoding='utf-8'))

    def errors(self, phase='close'):
        return checker.validate(self.record, self.root, phase)

    def rejects(self, fragment):
        self.assertTrue(any(fragment in message for message in self.errors()), self.errors())

    def cli(self, text):
        record_path = self.root / 'input.json'
        record_path.write_text(text, encoding='utf-8')
        return subprocess.run([sys.executable, str(SCRIPT), str(record_path), '--phase', 'close'],
                              text=True, capture_output=True, timeout=10)

    def test_valid_close(self):
        self.assertEqual([], self.errors())

    def test_valid_diagnosis_does_not_require_fix(self):
        self.record['mode'], self.record['status'] = 'diagnose', 'supported'
        for field in ('fix', 'checks', 'release', 'limitations'):
            del self.record[field]
        self.assertEqual([], self.errors('diagnose'))

    def test_template_is_not_accepted(self):
        self.record = json.loads((ROOT / 'templates' / 'evidence.json').read_text(encoding='utf-8'))
        self.assertTrue(self.errors())

    def test_unverified_cause(self):
        self.record['causality']['status'] = 'unverified'
        self.rejects('causality.status')

    def test_mitigation_is_not_root_fix(self):
        self.record['mode'], self.record['status'] = 'mitigate', 'mitigated'
        self.rejects('close requires')

    def test_placeholder_rejected(self):
        self.record['causality']['mechanism'] = '<待填写机制>'
        self.rejects('mechanism must contain real text')

    def test_missing_contract_evidence(self):
        self.record['expected']['source_refs'] = []
        self.rejects('expected.source_refs')

    def test_unknown_reference(self):
        self.record['causality']['evidence_refs'] = ['nonexistent']
        self.rejects('unknown evidence reference')

    def test_duplicate_evidence_identifier(self):
        self.record['evidence'].append(copy.deepcopy(self.record['evidence'][0]))
        self.rejects('duplicate evidence id')

    def test_missing_file(self):
        (self.root / 'buggy.py').unlink()
        self.rejects('missing/unsafe evidence path')

    def test_tampered_file(self):
        with (self.root / 'buggy.py').open('a') as stream:
            stream.write('\n# tampered\n')
        self.rejects('sha256 mismatch')

    def test_path_traversal(self):
        self.record['evidence'][0]['path'] = '../outside.md'
        self.rejects('missing/unsafe evidence path')

    def test_absolute_path(self):
        self.record['evidence'][0]['path'] = str(self.root / 'contract.md')
        self.rejects('missing/unsafe evidence path')

    def test_symlink_escape(self):
        outside = Path(self.temp.name) / 'outside.md'
        outside.write_text('not within trusted root')
        (self.root / 'escape.md').symlink_to(outside)
        self.record['evidence'][0]['path'] = 'escape.md'
        self.rejects('missing/unsafe evidence path')

    def test_empty_experiment(self):
        self.record['causality']['experiment'] = {}
        self.rejects('experiment.prediction')

    def test_no_red_test(self):
        self.record['checks'] = self.record['checks'][1:]
        self.rejects('matched regression red/green')

    def test_red_green_case_mismatch(self):
        self.record['checks'][1]['case'] = 'different-business-assertion'
        self.rejects('matched regression red/green')

    def test_red_green_environment_mismatch(self):
        self.record['checks'][1]['environment'] = 'different-runtime'
        self.rejects('matched regression red/green')

    def test_red_green_same_version(self):
        self.record['checks'][0]['version'] = self.record['fix']['version']
        self.rejects('matched regression red/green')

    def test_green_wrong_fixed_version(self):
        self.record['fix']['version'] = 'different-fix'
        self.rejects('matched regression red/green')

    def test_inconsistent_exit_code(self):
        self.record['checks'][1]['exit_code'] = 1
        self.rejects('inconsistent exit code')

    def test_boolean_not_valid_exit_code(self):
        self.record['checks'][1]['exit_code'] = False
        self.rejects('inconsistent exit code')

    def test_post_fix_failure_blocks_close(self):
        self.record['checks'][2]['outcome'] = 'failed'
        self.record['checks'][2]['exit_code'] = 1
        self.rejects('required post-fix check did not pass')

    def test_post_fix_not_run_blocks_close(self):
        self.record['checks'][2]['outcome'] = 'not_run'
        self.record['checks'][2]['exit_code'] = None
        self.rejects('required post-fix check did not pass')

    def test_high_risk_requires_counterfactual(self):
        self.record['checks'] = self.record['checks'][:-1]
        self.rejects('high risk needs matched failing counterfactual')

    def test_counterfactual_wrong_case(self):
        self.record['checks'][-1]['case'] = 'unrelated-failure'
        self.rejects('high risk needs matched failing counterfactual')

    def test_standard_risk_without_counterfactual(self):
        self.record['risk'] = 'standard'
        self.record['checks'] = self.record['checks'][:-1]
        self.assertEqual([], self.errors())

    def test_real_boundary_requires_integration(self):
        self.record['checks'] = [x for x in self.record['checks'] if x['kind'] != 'integration']
        self.rejects('need passing fixed-version integration')

    def test_no_boundary_integration_optional(self):
        self.record['impact']['boundaries'] = []
        self.record['checks'] = [x for x in self.record['checks'] if x['kind'] != 'integration']
        self.assertEqual([], self.errors())

    def test_neighbor_requires_same_environment(self):
        self.record['checks'][2]['environment'] = 'another environment'
        self.rejects('need passing fixed-version neighbor')

    def test_tests_need_log_not_only_source(self):
        self.record['checks'][1]['evidence_refs'] = ['E-CODE']
        self.rejects('needs evidence of kind log/observation')

    def test_guard_needs_source_or_diff(self):
        self.record['fix']['guard']['evidence_refs'] = ['E-RED']
        self.rejects('guard needs evidence of kind code/diff')

    def test_missing_limitations(self):
        self.record['limitations'] = []
        self.rejects('limitations must be a list')

    def test_malformed_objects_do_not_crash(self):
        for key in ('causality', 'checks', 'evidence', 'fix', 'impact', 'expected', 'reproduction'):
            for value in (None, 1, 'bad', [], {'bad': 1}):
                with self.subTest(key=key, value=value):
                    modified = copy.deepcopy(self.record)
                    modified[key] = value
                    self.assertTrue(checker.validate(modified, self.root, 'close'))

    def test_cli_success(self):
        result = self.cli(json.dumps(self.record))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn('mechanical evidence checks only', result.stdout)

    def test_cli_incomplete_record_exit_one(self):
        self.record['status'] = 'unverified'
        self.assertEqual(1, self.cli(json.dumps(self.record)).returncode)

    def test_cli_invalid_json_exit_two(self):
        self.assertEqual(2, self.cli('{invalid').returncode)

    def test_cli_duplicate_json_key_exit_two(self):
        self.assertEqual(2, self.cli('{"id":"a","id":"b"}').returncode)

    def test_recorded_commands_never_execute(self):
        sentinel = self.root / 'must-not-exist.txt'
        payload = "python3 -c \"from pathlib import Path; Path(%r).write_text('bad')\"" % str(sentinel)
        self.record['reproduction']['command'] = payload
        for check in self.record['checks']:
            check['command'] = payload
        self.assertEqual(0, self.cli(json.dumps(self.record)).returncode)
        self.assertFalse(sentinel.exists())


if __name__ == '__main__':
    unittest.main()
