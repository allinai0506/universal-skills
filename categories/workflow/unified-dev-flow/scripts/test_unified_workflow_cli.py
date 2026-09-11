#!/usr/bin/env python3
"""Subprocess contracts for the public CLI, with real temporary Git projects."""
import fcntl
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from test_unified_workflow_model import valid_route, valid_task
from unified_workflow.commands import Command
from unified_workflow.model import WorkspaceRevision, canonical_json, canonical_sha256
from unified_workflow.providers.trusted_local import TrustedLocalVerifier
from unified_workflow.store import ObserveRequest, RunStore


WRAPPER = Path(__file__).parent / "unified-workflow"


class CLIProject(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        self.documents = Path(self.temp.name) / "documents"
        self.documents.mkdir()
        self.counter = 0
        self.root.joinpath("input.txt").write_text("pass\n")
        self.root.joinpath("check.py").write_text(
            "from pathlib import Path\n"
            "p = Path('.unified-dev-flow/calls')\n"
            "p.write_text(p.read_text() + 'call\\n' if p.exists() else 'call\\n')\n"
            "assert Path('input.txt').read_text().startswith('pass')\n")
        for args in (("init", "-q"), ("config", "user.email", "test@example.invalid"),
                     ("config", "user.name", "CLI Test"), ("add", "."),
                     ("commit", "-qm", "baseline")):
            subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def document(self, value):
        self.counter += 1
        path = self.documents / f"document-{self.counter}.json"
        path.write_text(canonical_json(value), encoding="utf-8")
        return str(path)

    def call(self, *args, code=0, request=None, json_output=True):
        command = [str(WRAPPER), *args, "--project-root", str(self.root), "--work-id", "work-1"]
        if request:
            command += ["--request-id", request]
        if json_output:
            command += ["--json"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        if not json_output:
            return result.stdout
        self.assertEqual(result.stderr, "")
        parsed = json.loads(result.stdout)
        self.assertEqual(result.stdout, json.dumps(parsed, ensure_ascii=False, sort_keys=True,
                                                  separators=(",", ":"), allow_nan=False) + "\n")
        return parsed

    def mutate(self, *args, code=0, request=None):
        self.counter += 1
        return self.call(*args, code=code, request=request or f"request-{self.counter}")

    def initialize(self):
        return self.mutate("init", "--route-file", self.document(valid_route()))

    def add(self, identifier="A", dependencies=()):
        raw = valid_task()
        raw.update(task_id=identifier, dependencies=list(dependencies),
                   write_scope={"allowed_paths": ["input.txt", "check.py"], "forbidden_paths": []},
                   verification_inputs=["input.txt", "check.py"])
        raw["verification_commands"][0]["argv"] = [sys.executable, "check.py"]
        self.mutate("task", "add", "--task-file", self.document(raw))

    def start(self, identifier="A"):
        self.mutate("task", "ready", "--task-id", identifier)
        self.mutate("task", "start", "--task-id", identifier)

    def store(self):
        store = RunStore(self.root, "work-1")
        return store, store.load()

    def observation(self, identifier="A"):
        _, state = self.store()
        task = state.tasks[identifier]
        return TrustedLocalVerifier(self.root, task.contract).observe_workspace(
            ObserveRequest(task.contract, WorkspaceRevision.from_dict(json.loads(canonical_json(task.scope_origin)))))

    def review(self, identifier="A"):
        _, state = self.store()
        task = state.tasks[identifier]
        from unified_workflow.gate_kernel import fresh_evidence
        observed = self.observation(identifier)
        raw = dict(schema_version=1, task_id=identifier, task_revision=task.task_revision,
                   reviewer="human-reviewer", provider="external", provenance="human",
                   task_contract_sha256=canonical_sha256(task.contract.to_dict()),
                   source_fingerprint=observed.verification_input_fingerprint,
                   test_fingerprint=canonical_sha256([c.to_dict() for c in task.contract.verification_commands]),
                   evidence_fingerprint=canonical_sha256([e.evidence_sha256 for e in fresh_evidence(task, observed)]),
                   verdict="MERGE_READY", findings=[], reviewed_at="2026-09-11T00:00:00Z")
        return {**raw, "assertion_sha256": canonical_sha256(raw)}

    def reserve_verification(self, request="interrupted"):
        store, state = self.store()
        cmd = Command.from_dict(dict(schema_version=1, request_id=request,
            command_type="RECORD_VERIFICATION", work_id="work-1", task_id="A",
            actor={"type": "cli", "id": "local"}, expected_sequence=store.sequence, payload={"command_id": "unit"}))
        with patch.object(TrustedLocalVerifier, "run_verification", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                store.execute_verification(cmd, TrustedLocalVerifier(self.root, state.tasks["A"].contract))
        return cmd


class CLITests(CLIProject):
    def test_init_duplicate_identical_even_after_later_mutation(self):
        route = self.document(valid_route())
        first = self.mutate("init", "--route-file", route, request="init")
        self.add()
        before = self.store()[0].events_path.read_bytes()
        second = self.mutate("init", "--route-file", route, request="init")
        self.assertEqual(first, second)
        self.assertEqual(before, self.store()[0].events_path.read_bytes())

    def test_patch_init_denied_without_runtime_artifacts(self):
        route = valid_route()
        route["delivery_target"] = "patch"
        output = self.mutate("init", "--route-file", self.document(route), code=3)
        self.assertEqual(output["reason_code"], "RUNTIME_NOT_AUTHORIZED")
        self.assertFalse((self.root / ".unified-dev-flow").exists())

    def test_schema_and_arguments_fail_with_json_exit_two(self):
        route = valid_route()
        route["schema_version"] = 999
        self.mutate("init", "--route-file", self.document(route), code=2)
        self.call("init", "--route-file", self.document(valid_route()), code=2)
        self.call("transition", code=2)
        self.call("verify", "--command", "echo bypass", code=2)
        self.assertFalse((self.root / ".unified-dev-flow").exists())

    def test_invalid_json_and_missing_file(self):
        path = self.documents / "bad.json"
        for content in ('{"x":1,"x":2}', '{', 'NaN'):
            path.write_text(content)
            self.mutate("init", "--route-file", str(path), code=2)
        self.mutate("init", "--route-file", str(self.documents / "missing"), code=2)

    def test_corrupt_log_exit_four(self):
        self.initialize()
        self.store()[0].events_path.write_bytes(b"broken\n")
        result = self.call("status", code=4)
        self.assertEqual(result["reason_code"], "EVENT_JSON_CORRUPT")

    def test_invalid_event_schema_is_corrupt_state(self):
        self.initialize()
        path = self.store()[0].events_path
        event = json.loads(path.read_text())
        event["schema_version"] = 999
        path.write_text(json.dumps(event) + "\n")
        self.call("replay", code=4)

    def test_patch_init_with_existing_invalid_event_schema_exits_four(self):
        self.initialize()
        path = self.store()[0].events_path
        event = json.loads(path.read_text())
        event["schema_version"] = 999
        path.write_text(json.dumps(event) + "\n")
        before = path.read_bytes()
        route = valid_route()
        route["delivery_target"] = "patch"
        self.mutate("init", "--route-file", self.document(route), code=4)
        self.assertEqual(before, path.read_bytes())

    def test_busy_lock_exit_five(self):
        self.initialize()
        with self.store()[0].lock_path.open("rb") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.call("status", code=5)
        self.assertEqual(result["reason_code"], "LOCK_BUSY")

    def test_unregistered_verification_exits_six_without_execution(self):
        self.initialize()
        self.add()
        self.start()
        self.mutate("verify", "--task-id", "A", "--command-id", "unregistered", code=6)
        self.assertFalse((self.root / ".unified-dev-flow/calls").exists())

    def test_verification_retry_does_not_run_twice(self):
        self.initialize()
        self.add()
        self.start()
        first = self.mutate("verify", "--task-id", "A", "--command-id", "unit", request="verify")
        before = self.store()[0].events_path.read_bytes()
        retry = self.mutate("verify", "--task-id", "A", "--command-id", "unit", request="verify")
        self.assertEqual(first, retry)
        self.assertEqual(before, self.store()[0].events_path.read_bytes())
        self.assertEqual((self.root / ".unified-dev-flow/calls").read_text(), "call\n")

    def test_in_doubt_status_retry_and_audited_resolution(self):
        self.initialize()
        self.add()
        self.start()
        self.reserve_verification()
        result = self.call("request", "status", "--request-id", "interrupted", code=7)
        self.assertEqual(result["request"]["status"], "in_doubt")
        self.mutate("verify", "--task-id", "A", "--command-id", "unit", request="interrupted", code=7)
        self.assertFalse((self.root / ".unified-dev-flow/calls").exists())
        resolution = self.document({"outcome": "abandoned", "actor": {"type": "human", "id": "operator"}, "note": "Checked process; abandoned."})
        self.mutate("request", "resolve", "--resolution-file", resolution, request="interrupted")
        result = self.call("request", "status", "--request-id", "interrupted")
        self.assertEqual(result["request"]["outcome"], "abandoned")

    def test_status_replay_do_not_touch_other_control_directories(self):
        self.initialize()
        for path in (".omc", ".superpowers/sdd", ".codegraph"):
            folder = self.root / path
            folder.mkdir(parents=True)
            folder.joinpath("sentinel").write_bytes(b"unchanged")
        before = {str(p): (p.stat().st_mtime_ns, p.read_bytes()) for p in self.root.rglob("sentinel")}
        self.assertEqual(self.call("status"), self.call("replay"))
        after = {str(p): (p.stat().st_mtime_ns, p.read_bytes()) for p in self.root.rglob("sentinel")}
        self.assertEqual(before, after)
        self.assertEqual(len(list(self.root.rglob("sentinel"))), 3)

    def test_manually_resolved_provider_failure_keeps_exit_six_on_retry(self):
        self.initialize()
        self.add()
        self.start()
        self.reserve_verification()
        resolution = self.document({"outcome": "provider_failure",
            "actor": {"type": "human", "id": "operator"}, "note": "Confirmed process failed to start."})
        self.mutate("request", "resolve", "--resolution-file", resolution, request="interrupted")
        self.mutate("verify", "--task-id", "A", "--command-id", "unit", request="interrupted", code=6)
        self.assertFalse((self.root / ".unified-dev-flow/calls").exists())

    def test_sequence_and_text_reason(self):
        self.initialize()
        output = self.mutate("run", "complete", "--expected-sequence", "0", code=3)
        self.assertEqual(output["reason_code"], "EXPECTED_SEQUENCE_MISMATCH")
        text = self.call("run", "complete", request="text-denial", code=3, json_output=False)
        self.assertIn("EVIDENCE_MISSING", text)

    def test_review_retry_after_wait_was_already_committed(self):
        self.initialize()
        self.add()
        self.start()
        self.mutate("verify", "--task-id", "A", "--command-id", "unit")
        store, _ = self.store()
        wait_id = "review-wait-" + canonical_sha256("review").removeprefix("sha256:")
        store.execute(Command.from_dict(dict(schema_version=1, request_id=wait_id,
            command_type="WAIT_FOR_REVIEW", work_id="work-1", task_id="A", actor={"type": "cli", "id": "local"},
            expected_sequence=store.sequence, payload={})), self.observation())
        self.add("B")  # Another mutation after the interrupted, durable wait.
        assertion = self.document(self.review())
        first = self.mutate("review", "record", "--task-id", "A", "--assertion-file", assertion, request="review")
        before = store.events_path.read_bytes()
        self.assertEqual(first, self.mutate("review", "record", "--task-id", "A", "--assertion-file", assertion, request="review"))
        self.assertEqual(before, store.events_path.read_bytes())
        self.mutate("task", "accept", "--task-id", "A")

    def test_review_with_explicit_sequence_retries_identically(self):
        self.initialize()
        self.add()
        self.start()
        self.mutate("verify", "--task-id", "A", "--command-id", "unit")
        sequence = str(self.store()[0].sequence)
        assertion = self.document(self.review())
        args = ("review", "record", "--task-id", "A", "--assertion-file", assertion,
                "--expected-sequence", sequence)
        first = self.mutate(*args, request="explicit-review")
        before = self.store()[0].events_path.read_bytes()
        self.assertEqual(first, self.mutate(*args, request="explicit-review"))
        self.assertEqual(before, self.store()[0].events_path.read_bytes())

    def test_wait_denial_is_queryable_and_reserves_full_review_identity(self):
        self.initialize()
        self.add()
        self.start()
        assertion = self.review()
        path = self.document(assertion)
        result = self.mutate("review", "record", "--task-id", "A", "--assertion-file", path,
                             request="denied-review", code=3)
        self.assertEqual(result["reason_code"], "EVIDENCE_MISSING")
        status = self.call("request", "status", "--request-id", "denied-review")
        self.assertEqual(status["request"]["outcome"], "denied")
        self.assertEqual(status["request"]["reason_code"], "EVIDENCE_MISSING")
        before = self.store()[0].events_path.read_bytes()
        self.assertEqual(result, self.mutate("review", "record", "--task-id", "A", "--assertion-file", path,
                                             request="denied-review", code=3))
        conflict = self.mutate("task", "start", "--task-id", "A", request="denied-review", code=3)
        self.assertEqual(conflict["reason_code"], "IDEMPOTENCY_CONFLICT")
        assertion["reviewer"] = "changed-reviewer"
        assertion.pop("assertion_sha256")
        assertion["assertion_sha256"] = canonical_sha256(assertion)
        conflict = self.mutate("review", "record", "--task-id", "A", "--assertion-file", self.document(assertion),
                               request="denied-review", code=3)
        self.assertEqual(conflict["reason_code"], "IDEMPOTENCY_CONFLICT")
        self.assertEqual(before, self.store()[0].events_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
