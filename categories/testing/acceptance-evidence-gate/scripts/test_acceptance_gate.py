#!/usr/bin/env python3
"""Integration checks: real Git repo + real subprocess executions, no network."""

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

GATE = Path(__file__).with_name("acceptance_gate.py")


class AcceptanceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gate-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "gate@example.invalid")
        self.git("config", "user.name", "Gate Test")
        (self.repo / "feature.txt").write_text("works", encoding="utf-8")
        (self.repo / "test_acceptance_case.py").write_text(
            "import unittest\nfrom pathlib import Path\n"
            "class Acceptance(unittest.TestCase):\n"
            "  def test_feature(self):\n"
            "    self.assertEqual((Path(__file__).parent / 'feature.txt').read_text(), 'works')\n",
            encoding="utf-8",
        )
        self.git("add", ".")
        self.git("commit", "-qm", "initial")
        self.contract = self.root / "contract.json"
        self.out = self.root / "evidence"
        self.spec = {
            "schema_version": 1, "work_item": "CASE-123",
            "criteria": [{"id": "AC-01", "description": "Feature reads works",
                          "source": "issue", "source_ref": "CASE-123#AC1",
                          "check_ids": ["acceptance-case"]}],
            "checks": [{"id": "acceptance-case", "kind": "acceptance",
                        "argv": [sys.executable, "-m", "unittest", "test_acceptance_case.py"],
                        "timeout_seconds": 30}],
        }
        self.write_contract()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              text=True, capture_output=True, check=True)

    def write_contract(self):
        self.contract.write_text(json.dumps(self.spec), encoding="utf-8")

    def run_gate(self):
        return subprocess.run([sys.executable, str(GATE), "run", "--repo", str(self.repo),
                               "--contract", str(self.contract), "--out", str(self.out)],
                              text=True, capture_output=True, check=False)

    def verify_gate(self):
        return subprocess.run([sys.executable, str(GATE), "verify", "--repo", str(self.repo),
                               "--contract", str(self.contract),
                               "--receipt", str(self.out / "receipt.json")],
                              text=True, capture_output=True, check=False)

    def test_success_and_criterion_mapping(self):
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        verify = self.verify_gate()
        self.assertEqual(verify.returncode, 0, verify.stderr + verify.stdout)
        self.assertIn("GATE: PASS", verify.stdout)

    def test_failed_acceptance_blocks(self):
        self.spec["checks"][0]["argv"] = [sys.executable, "-c", "raise SystemExit(9)"]
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 1)
        self.assertEqual(self.verify_gate().returncode, 1)

    def test_dirty_before_run_blocks(self):
        (self.repo / "feature.txt").write_text("not works", encoding="utf-8")
        self.assertEqual(self.run_gate().returncode, 2)

    def test_dirty_after_run_blocks(self):
        self.assertEqual(self.run_gate().returncode, 0)
        (self.repo / "feature.txt").write_text("not works", encoding="utf-8")
        self.assertEqual(self.verify_gate().returncode, 1)

    def test_new_commit_invalidates_receipt(self):
        self.assertEqual(self.run_gate().returncode, 0)
        (self.repo / "readme.txt").write_text("updated", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "subsequent")
        self.assertEqual(self.verify_gate().returncode, 1)

    def test_changed_contract_invalidates_receipt(self):
        self.assertEqual(self.run_gate().returncode, 0)
        self.spec["criteria"][0]["description"] = "Changed requirement"
        self.write_contract()
        self.assertEqual(self.verify_gate().returncode, 1)

    def test_tampered_log_invalidates_receipt(self):
        self.assertEqual(self.run_gate().returncode, 0)
        with (self.out / "logs" / "acceptance-case.log").open("a") as f:
            f.write("tamper\n")
        self.assertEqual(self.verify_gate().returncode, 1)

    def test_no_acceptance_check_rejected(self):
        self.spec["checks"][0]["kind"] = "build"
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 2)

    def test_expired_receipt_rejected(self):
        self.assertEqual(self.run_gate().returncode, 0)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt["started_at"] = "2020-01-01T00:00:00+00:00"
        receipt["finished_at"] = "2020-01-01T00:01:00+00:00"
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        self.assertEqual(self.verify_gate().returncode, 1)

    def test_timeout_blocks(self):
        self.spec["checks"][0]["argv"] = [sys.executable, "-c", "import time; time.sleep(2)"]
        self.spec["checks"][0]["timeout_seconds"] = 1
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 1)
        self.assertEqual(self.verify_gate().returncode, 1)

    def test_tampered_exit_code_invalidates_receipt(self):
        """Flipping a failing exit_code to 0 must not make the gate pass."""
        self.spec["checks"][0]["argv"] = [sys.executable, "-c", "raise SystemExit(9)"]
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 1)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt["checks"][0]["exit_code"] = 0
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        verify = self.verify_gate()
        self.assertEqual(verify.returncode, 1)
        self.assertIn("digest mismatch", verify.stderr)

    def test_receipt_digest_present(self):
        self.assertEqual(self.run_gate().returncode, 0)
        receipt = json.loads((self.out / "receipt.json").read_text(encoding="utf-8"))
        self.assertIn("receipt_sha256", receipt)

    def test_vacuous_acceptance_check_rejected(self):
        for argv in (["true"], ["echo", "ok"], [sys.executable, "-c", "pass"]):
            with self.subTest(argv=argv):
                self.spec["checks"][0]["argv"] = argv
                self.write_contract()
                self.assertEqual(self.run_gate().returncode, 2)

    def test_vacuous_non_acceptance_check_allowed(self):
        """A build-kind smoke check may legitimately be a no-op."""
        self.spec["checks"].append({"id": "smoke", "kind": "build", "argv": ["true"],
                                    "timeout_seconds": 10})
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 0)
        self.assertEqual(self.verify_gate().returncode, 0)

    def test_timeout_kills_grandchildren(self):
        """A timed-out check must not leave orphaned child processes running."""
        marker = self.root / "grandchild-ran.txt"
        script = (
            "import subprocess, sys, time\n"
            f"subprocess.Popen([sys.executable, '-c', "
            f"\"import time,pathlib; time.sleep(3); pathlib.Path({str(marker)!r}).write_text('x')\"])\n"
            "time.sleep(5)\n"
        )
        self.spec["checks"][0]["argv"] = [sys.executable, "-c", script]
        self.spec["checks"][0]["timeout_seconds"] = 1
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 1)
        time.sleep(4)
        self.assertFalse(marker.exists(), "grandchild survived the timeout")

    def test_missing_receipt_digest_rejected(self):
        self.assertEqual(self.run_gate().returncode, 0)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt.pop("receipt_sha256", None)
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        verify = self.verify_gate()
        self.assertEqual(verify.returncode, 1)
        self.assertIn("digest missing", verify.stderr)


if __name__ == "__main__":
    unittest.main()
