#!/usr/bin/env python3
"""Integration checks: real Git repo + real subprocess executions, no network."""

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from acceptance_gate import RECEIPT_DIGEST_FIELD, receipt_digest  # noqa: E402

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

    def run_gate(self, out=None):
        """Run the gate. Each call needs a fresh output directory, otherwise the
        second run is rejected with "output directory is not empty"."""
        return subprocess.run([sys.executable, str(GATE), "run", "--repo", str(self.repo),
                               "--contract", str(self.contract), "--out", str(out or self.out)],
                              text=True, capture_output=True, check=False)

    def verify_gate(self, anchor=None):
        cmd = [sys.executable, str(GATE), "verify", "--repo", str(self.repo),
               "--contract", str(self.contract),
               "--receipt", str(self.out / "receipt.json")]
        if anchor is not None:
            cmd += ["--anchor", str(anchor)]
        return subprocess.run(cmd, text=True, capture_output=True, check=False)

    def anchor_gate(self, anchor, contract=None):
        # `contract` may legitimately be an empty string (a negative test), so
        # use an explicit None check rather than `or`.
        chosen = self.contract if contract is None else contract
        return subprocess.run([sys.executable, str(GATE), "anchor", "--repo", str(self.repo),
                               "--receipt", str(self.out / "receipt.json"),
                               "--contract", str(chosen),
                               "--anchor", str(anchor)],
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
        for argv in (["true"], ["echo", "ok"], [sys.executable, "-c", "pass"],
                     ["sh", "-c", "true"], ["/bin/sh", "-c", "echo ok"],
                     [sys.executable, "-c", "import sys; sys.exit(0)"],
                     [sys.executable, "-c", "raise SystemExit(0)"],
                     [sys.executable, "-c", "Raise SystemExit(0)"],
                     [sys.executable, "-c", "import os; os._exit(0)"]):
            with self.subTest(argv=argv):
                self.spec["checks"][0]["argv"] = argv
                self.write_contract()
                self.assertEqual(self.run_gate().returncode, 2)

    def test_meaningful_shell_snippet_not_rejected(self):
        """A chained shell snippet runs a real command and must not be rejected.

        The point of the check is that the *contract loads* (no vacuous
        rejection); the command then runs and must pass.
        """
        for index, argv in enumerate(
                (["sh", "-c", "echo banner; " + sys.executable + " -m unittest test_acceptance_case.py"],
                 ["sh", "-c", "echo x && " + sys.executable + " -m unittest test_acceptance_case.py"],
                 ["sh", "-c", sys.executable + " -m unittest test_acceptance_case.py"])):
            with self.subTest(argv=argv):
                self.spec["checks"][0]["argv"] = argv
                self.write_contract()
                out = self.root / f"evidence-shell-{index}"
                self.assertEqual(self.run_gate(out=out).returncode, 0)

    def test_broken_receipt_is_gate_failure_not_invalid_input(self):
        """A structurally broken receipt is a failed gate (exit 1), not exit 2."""
        self.assertEqual(self.run_gate().returncode, 0)
        receipt_file = self.out / "receipt.json"
        receipt_file.write_text("{not json", encoding="utf-8")
        verify = self.verify_gate()
        self.assertEqual(verify.returncode, 1)
        self.assertIn("not valid JSON", verify.stderr)

    def test_receipt_with_non_list_checks_is_gate_failure(self):
        self.assertEqual(self.run_gate().returncode, 0)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt["checks"] = {"a1": {}}
        receipt[RECEIPT_DIGEST_FIELD] = receipt_digest(receipt)
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        verify = self.verify_gate()
        self.assertEqual(verify.returncode, 1)
        self.assertIn("receipt.checks must be a list", verify.stderr)

    def test_anchor_validates_receipt(self):
        """A matching anchor lets verify pass; the anchor commits to the receipt."""
        self.assertEqual(self.run_gate().returncode, 0)
        anchor = self.root / "anchor" / "evidence.json"
        anchored = self.anchor_gate(anchor)
        self.assertEqual(anchored.returncode, 0, anchored.stderr + anchored.stdout)
        verify = self.verify_gate(anchor=anchor)
        self.assertEqual(verify.returncode, 0, verify.stderr + verify.stdout)

    def test_anchor_detects_forged_receipt(self):
        """Forge a receipt after an honest anchor, keep the honest anchor.

        The anchor is created for a *passing* receipt; afterwards the receipt
        is edited (and its digest recomputed), so the anchor no longer
        commits to it.
        """
        self.assertEqual(self.run_gate().returncode, 0)
        anchor = self.root / "anchor" / "evidence.json"
        self.assertEqual(self.anchor_gate(anchor).returncode, 0)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt["checks"][0]["exit_code"] = 7
        receipt[RECEIPT_DIGEST_FIELD] = receipt_digest(receipt)
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        verify = self.verify_gate(anchor=anchor)
        self.assertEqual(verify.returncode, 1)
        self.assertIn("anchor does not commit to this receipt", verify.stderr)

    def test_anchor_detects_moved_head(self):
        """The anchor binds the receipt to a HEAD; a later commit invalidates it."""
        self.assertEqual(self.run_gate().returncode, 0)
        anchor = self.root / "anchor" / "evidence.json"
        self.assertEqual(self.anchor_gate(anchor).returncode, 0)
        (self.repo / "readme.txt").write_text("moved", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "after anchoring")
        verify = self.verify_gate(anchor=anchor)
        self.assertEqual(verify.returncode, 1)
        self.assertIn("anchor HEAD mismatch", verify.stderr)

    def test_anchor_missing_is_a_failure(self):
        self.assertEqual(self.run_gate().returncode, 0)
        verify = self.verify_gate(anchor=self.root / "nope" / "missing.json")
        self.assertEqual(verify.returncode, 1)
        self.assertIn("anchor unreadable", verify.stderr)

    def test_anchor_rejects_receipt_without_digest(self):
        self.assertEqual(self.run_gate().returncode, 0)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt.pop(RECEIPT_DIGEST_FIELD, None)
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        anchored = self.anchor_gate(self.root / "anchor" / "evidence.json")
        self.assertEqual(anchored.returncode, 2)
        self.assertIn("receipt has no digest", anchored.stderr)

    def test_anchor_is_write_once(self):
        """An existing anchor is never overwritten: a commitment cannot be replaced."""
        self.assertEqual(self.run_gate().returncode, 0)
        anchor = self.root / "anchor" / "evidence.json"
        self.assertEqual(self.anchor_gate(anchor).returncode, 0)
        first = json.loads(anchor.read_text(encoding="utf-8"))
        again = self.anchor_gate(anchor)
        self.assertEqual(again.returncode, 2)
        self.assertIn("anchor already exists", again.stderr)
        self.assertEqual(json.loads(anchor.read_text(encoding="utf-8")), first)

    def test_anchor_detects_a_swapped_anchor(self):
        """An anchor issued for a different receipt must not validate this one.

        `anchor` now refuses a receipt whose HEAD is no longer current, so the
        swap is caught at stamping time rather than at verify time.
        """
        self.assertEqual(self.run_gate().returncode, 0)
        other = self.root / "other"
        other.mkdir()
        (other / "f.txt").write_text("other", encoding="utf-8")
        subprocess.run(["git", "-C", str(other), "init", "-q"], check=False)
        subprocess.run(["git", "-C", str(other), "config", "user.email", "a@b.c"], check=False)
        subprocess.run(["git", "-C", str(other), "config", "user.name", "t"], check=False)
        subprocess.run(["git", "-C", str(other), "add", "."], check=False)
        subprocess.run(["git", "-C", str(other), "commit", "-qm", "other"], check=False)
        anchor = self.root / "anchor" / "swapped.json"
        anchored = subprocess.run(
            [sys.executable, str(GATE), "anchor", "--repo", str(other),
             "--receipt", str(self.out / "receipt.json"),
             "--contract", str(self.contract),
             "--anchor", str(anchor)],
            text=True, capture_output=True, check=False)
        self.assertEqual(anchored.returncode, 2)
        self.assertIn("HEAD/state mismatch", anchored.stderr)

    def test_agent_can_forge_its_own_anchor(self):
        """Documented limit: the Agent can write an anchor that commits to a forged
        receipt.

        `verify --anchor` therefore adds no protection on its own — the whole
        value comes from the anchor living somewhere the Agent cannot write.
        This test pins that limit so it cannot be silently "fixed" by someone
        who believes the anchor is self-authenticating.
        """
        self.spec["checks"][0]["argv"] = [sys.executable, "-c", "raise SystemExit(9)"]
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 1)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt["checks"][0]["exit_code"] = 0
        receipt[RECEIPT_DIGEST_FIELD] = receipt_digest(receipt)
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        # The Agent forges an anchor that commits to its forged receipt.
        head = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"],
                               capture_output=True, text=True, check=False).stdout.strip()
        forged = self.root / "agent-written-anchor.json"
        forged.write_text(json.dumps({
            "schema": "acceptance-evidence-anchor/1",
            "work_item": receipt.get("work_item"),
            "repo_head": head,
            "receipt_sha256": receipt[RECEIPT_DIGEST_FIELD],
            "anchored_at": "2026-01-01T00:00:00+00:00",
        }), encoding="utf-8")
        verify = self.verify_gate(anchor=forged)
        self.assertEqual(verify.returncode, 0)
        self.assertIn("GATE: PASS", verify.stdout)

    def test_anchor_refuses_a_forged_receipt(self):
        """`anchor` must not stamp a receipt whose digest does not match its body."""
        # Start from a failing run so there is an exit_code to flip.
        self.spec["checks"][0]["argv"] = [sys.executable, "-c", "raise SystemExit(9)"]
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 1)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt["checks"][0]["exit_code"] = 0  # body edited, digest not recomputed
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        anchored = self.anchor_gate(self.root / "anchor" / "evidence.json")
        self.assertEqual(anchored.returncode, 2)
        self.assertIn("receipt digest mismatch", anchored.stderr)

    def test_anchor_refuses_receipt_from_another_head(self):
        """The anchor records the receipt's own HEAD; a moved repo is refused."""
        self.assertEqual(self.run_gate().returncode, 0)
        (self.repo / "readme.txt").write_text("moved", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "after run")
        anchored = self.anchor_gate(self.root / "anchor" / "evidence.json")
        self.assertEqual(anchored.returncode, 2)
        self.assertIn("HEAD/state mismatch", anchored.stderr)

    def test_anchor_refuses_a_fully_forged_receipt(self):
        """A receipt forged end-to-end (digest recomputed) must not be anchored.

        This is the case the first S6 round called a "rubber stamp": the
        forger rewrites the receipt *and* recomputes its digest, so a summary
        check alone cannot tell. `anchor` therefore applies the same judgement
        `verify` applies, and additionally reads the log — the independent
        trace of what the command actually did. The forged receipt claims
        exit 0 while the log still records the failure, so the log check
        catches it.
        """
        # A failing check that writes to its log, so the log carries the trace.
        self.spec["checks"][0]["argv"] = [sys.executable, "-c",
                                          "import sys; print('FAIL: forged'); sys.exit(9)"]
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 1)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt["checks"][0]["exit_code"] = 0
        receipt[RECEIPT_DIGEST_FIELD] = receipt_digest(receipt)
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        anchored = self.anchor_gate(self.root / "anchor" / "evidence.json")
        self.assertEqual(anchored.returncode, 2)
        self.assertIn("refusing to anchor", anchored.stderr)
        self.assertIn("log still records a failure", anchored.stderr)

    def test_anchor_refuses_a_receipt_with_a_tampered_log(self):
        """A receipt whose log no longer matches its digest must not be anchored."""
        self.assertEqual(self.run_gate().returncode, 0)
        with (self.out / "logs" / "acceptance-case.log").open("a") as f:
            f.write("tamper\n")
        anchored = self.anchor_gate(self.root / "anchor" / "evidence.json")
        self.assertEqual(anchored.returncode, 2)
        self.assertIn("refusing to anchor", anchored.stderr)

    def test_anchor_requires_a_contract(self):
        """An anchor must be bound to a contract, not stamped blindly."""
        self.assertEqual(self.run_gate().returncode, 0)
        proc = subprocess.run(
            [sys.executable, str(GATE), "anchor", "--repo", str(self.repo),
             "--receipt", str(self.out / "receipt.json"),
             "--anchor", str(self.root / "anchor" / "evidence.json")],
            text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--contract", proc.stderr)

    def test_anchor_accepts_a_passing_log_mentioning_failure_words(self):
        """Passing output that merely mentions failure words must not be rejected.

        Test output routinely says things like "previous AssertionError fixed"
        or "status: FAIL: none found". A bare substring match would refuse
        honest receipts, so the markers are matched at the start of a line.
        """
        self.spec["checks"][0]["argv"] = [sys.executable, "-c",
                                          "print('previous AssertionError fixed'); "
                                          "print('status: FAIL: none found'); "
                                          "print('processing ERROR: retrying')"]
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 0)
        anchored = self.anchor_gate(self.root / "anchor" / "evidence.json")
        self.assertEqual(anchored.returncode, 0, anchored.stderr + anchored.stdout)

    def test_anchor_rejects_a_log_whose_line_starts_with_a_failure_marker(self):
        """A log line that *starts* with a failure marker is a real failure."""
        self.spec["checks"][0]["argv"] = [sys.executable, "-c",
                                          "print('FAIL: forged'); import sys; sys.exit(9)"]
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 1)
        anchored = self.anchor_gate(self.root / "anchor" / "evidence.json")
        self.assertEqual(anchored.returncode, 2)
        self.assertIn("log still records a failure", anchored.stderr)

    def test_anchor_rejects_an_empty_contract_path(self):
        """An empty --contract must be rejected, not silently skipped."""
        self.assertEqual(self.run_gate().returncode, 0)
        anchored = self.anchor_gate(self.root / "anchor" / "evidence.json", contract="")
        self.assertEqual(anchored.returncode, 2)
        self.assertIn("--contract is required", anchored.stderr)

    def test_anchor_rejects_an_out_of_range_max_age(self):
        """anchor --max-age-hours is bounded like verify's."""
        self.assertEqual(self.run_gate().returncode, 0)
        proc = subprocess.run(
            [sys.executable, str(GATE), "anchor", "--repo", str(self.repo),
             "--receipt", str(self.out / "receipt.json"),
             "--contract", str(self.contract),
             "--anchor", str(self.root / "anchor" / "evidence.json"),
             "--max-age-hours", "999999"],
            text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--max-age-hours must be within", proc.stderr)

    def test_verify_rejects_empty_anchor(self):
        """An empty --anchor must be rejected, not silently ignored."""
        self.assertEqual(self.run_gate().returncode, 0)
        verify = self.verify_gate(anchor="")
        self.assertEqual(verify.returncode, 2)
        self.assertIn("--anchor must not be empty", verify.stderr)

    def test_anchor_refuses_path_inside_repository(self):
        """An anchor in the worktree would dirty it and break later verifies."""
        self.assertEqual(self.run_gate().returncode, 0)
        anchored = self.anchor_gate(self.repo / ".anchor" / "evidence.json")
        self.assertEqual(anchored.returncode, 2)
        self.assertIn("outside repository", anchored.stderr)

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

    def test_malformed_timestamp_is_gate_failure_not_invalid_input(self):
        """A broken timestamp is a failed gate (exit 1), not invalid input (exit 2)."""
        self.assertEqual(self.run_gate().returncode, 0)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt["finished_at"] = "not-a-timestamp"
        receipt[RECEIPT_DIGEST_FIELD] = receipt_digest(receipt)
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        verify = self.verify_gate()
        self.assertEqual(verify.returncode, 1)
        self.assertIn("timestamp missing or malformed", verify.stderr)

    def test_recomputed_digest_still_passes(self):
        """Documented limit: the digest is tamper-evident, not tamper-proof.

        A forger who rewrites the receipt can also recompute the digest, so
        the gate still reports PASS. This test pins that known limit so the
        behaviour cannot silently change, and keeps the trust boundary in
        references/verification-rules.md honest.
        """
        self.spec["checks"][0]["argv"] = [sys.executable, "-c", "raise SystemExit(9)"]
        self.write_contract()
        self.assertEqual(self.run_gate().returncode, 1)
        receipt_file = self.out / "receipt.json"
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt["checks"][0]["exit_code"] = 0
        receipt[RECEIPT_DIGEST_FIELD] = receipt_digest(receipt)
        receipt_file.write_text(json.dumps(receipt), encoding="utf-8")
        self.assertEqual(self.verify_gate().returncode, 0)


if __name__ == "__main__":
    unittest.main()
