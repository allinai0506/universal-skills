#!/usr/bin/env python3
"""Provider contracts exercised against a real Git worktree and child processes."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import unittest

from unified_workflow.model import TaskContract, WorkspaceRevision, canonical_sha256
from unified_workflow.providers import (MockProvider, ProviderError, TrustedLocalVerifier,
                                        VerificationResult)
from unified_workflow.providers.base import ObserveRequest


def task_dict(commands, inputs=("**/*",)):
    return {
        "schema_version": 1,
        "task_id": "task-001",
        "objective": "Verify a real local workspace.",
        "required": True,
        "dependencies": [],
        "write_scope": {"allowed_paths": ["**/*"], "forbidden_paths": [".git/**"]},
        "verification_inputs": list(inputs),
        "acceptance": ["Provider tests pass."],
        "verification_commands": commands,
        "proof_mode": "acceptance_test",
        "required_review": "none",
    }


def command(command_id, argv, cwd=".", timeout=2, limit=128):
    return {"command_id": command_id, "argv": argv, "cwd": cwd,
            "timeout_seconds": timeout, "max_output_bytes": limit,
            "required": True, "claims": ["deterministic"]}


def origin():
    return WorkspaceRevision.from_dict({
        "schema_version": 1, "provider": "origin", "revision_id": "origin-1",
        "verification_input_fingerprint": "sha256:" + "0" * 64, "changed_paths": [],
        "observed_at": "2026-09-11T00:00:00Z",
    })


def request_for(patterns=("**/*",), commands=()):
    return ObserveRequest(TaskContract.from_dict(task_dict(list(commands), patterns)), origin())


class MockProviderTests(unittest.TestCase):
    def test_consumes_observations_and_results_in_fifo_order(self):
        first = replace(origin(), revision_id="first")
        second = replace(origin(), revision_id="second")
        result = VerificationResult("2026-09-11T00:00:00Z", "2026-09-11T00:00:01Z", 0,
            False, False, b"ok", b"", 2, 0, sha256(b"ok").hexdigest(),
            sha256(b"").hexdigest())
        provider = MockProvider([first, second], [result])
        self.assertEqual(provider.observe_workspace(request_for()), first)
        self.assertEqual(provider.observe_workspace(request_for()), second)
        self.assertEqual(provider.run_verification("unit"), result)

    def test_reports_exhaustion_and_fixture_errors(self):
        provider = MockProvider([], [ProviderError("FIXTURE_FAILURE", "simulated")])
        with self.assertRaisesRegex(ProviderError, "MOCK_OBSERVATIONS_EXHAUSTED"):
            provider.observe_workspace(request_for())
        with self.assertRaisesRegex(ProviderError, "FIXTURE_FAILURE"):
            provider.run_verification("unit")
        with self.assertRaisesRegex(ProviderError, "MOCK_RESULTS_EXHAUSTED"):
            provider.run_verification("unit")


class TrustedLocalVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "test@example.invalid"],
                       check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Provider Test"],
                       check=True)
        (self.root / "src").mkdir()
        (self.root / "src" / "tracked.txt").write_text("before\n")
        subprocess.run(["git", "-C", str(self.root), "add", "src/tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "initial"], check=True)
        self.limit = 128
        self.full_output = b"x" * 1024
        self.commands = [
            command("large-output", [sys.executable, "-c",
                    "import sys; sys.stdout.write('x' * 1024); sys.stderr.write('e' * 512)"],
                    limit=self.limit),
            command("timeout", [sys.executable, "-c",
                    "import pathlib, subprocess, sys, time; child=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); pathlib.Path('child.pid').write_text(str(child.pid)); time.sleep(30)"],
                    timeout=1),
            command("parent-exits-child-holds-pipes", [sys.executable, "-c",
                    "import pathlib, subprocess, sys; child=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(3)']); pathlib.Path('pipe-child.pid').write_text(str(child.pid))"],
                    timeout=1),
            command("parent-closes-pipes", [sys.executable, "-c",
                    "import os, time; os.close(1); os.close(2); time.sleep(3)"], timeout=1),
            command("nonzero", [sys.executable, "-c", "import sys; sys.exit(7)"], limit=self.limit),
            command("environment", [sys.executable, "-c",
                    "import os,sys;sys.stdout.write(os.getenv('MARK', 'none') + '|' + os.getenv('LEAK', 'none'))"],
                    limit=self.limit),
        ]
        self.contract = TaskContract.from_dict(task_dict(self.commands))
        self.provider = TrustedLocalVerifier(self.root, self.contract, {"MARK": "present"})

    @staticmethod
    def local_origin():
        return WorkspaceRevision.from_dict({
            "schema_version": 1, "provider": "trusted-local", "revision_id": "origin-1",
            "verification_input_fingerprint": "sha256:" + "0" * 64, "changed_paths": [],
            "observed_at": "2026-09-11T00:00:00Z", "file_manifest": {},
        })

    def local_request(self, patterns=("**/*",)):
        return replace(request_for(patterns), scope_origin=self.local_origin())

    def test_local_verifier_rejects_unregistered_command(self):
        with self.assertRaisesRegex(ProviderError, "COMMAND_NOT_REGISTERED"):
            self.provider.run_verification("not-registered")

    def test_local_verifier_truncates_output_but_hashes_full_stream(self):
        result = self.provider.run_verification("large-output")
        self.assertTrue(result.output_truncated)
        self.assertEqual(len(result.stdout), self.limit)
        self.assertEqual(len(result.stderr), self.limit)
        self.assertEqual(result.stdout_bytes, len(self.full_output))
        self.assertEqual(result.stderr_bytes, 512)
        self.assertEqual(result.stdout_sha256, sha256(self.full_output).hexdigest())
        self.assertEqual(result.stderr_sha256, sha256(b"e" * 512).hexdigest())

    def test_timeout_kills_child_process_group(self):
        result = self.provider.run_verification("timeout")
        self.assertTrue(result.timed_out)
        self.assertIsNone(result.exit_code)
        child_pid = int((self.root / "child.pid").read_text())
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(.02)
        else:
            self.fail("timed-out child process remains alive")

    def test_timeout_deadline_kills_descendant_when_parent_exits_with_pipes_open(self):
        started = time.monotonic()
        result = self.provider.run_verification("parent-exits-child-holds-pipes")
        self.assertLess(time.monotonic() - started, 1.8)
        self.assertTrue(result.timed_out)
        child_pid = int((self.root / "pipe-child.pid").read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(child_pid, 0)

    def test_timeout_deadline_applies_after_parent_closes_pipes(self):
        started = time.monotonic()
        result = self.provider.run_verification("parent-closes-pipes")
        self.assertLess(time.monotonic() - started, 1.8)
        self.assertTrue(result.timed_out)

    def test_nonzero_exit_is_preserved(self):
        result = self.provider.run_verification("nonzero")
        self.assertFalse(result.timed_out)
        self.assertEqual(result.exit_code, 7)

    def test_cwd_escape_is_rejected_before_execution(self):
        escaped = replace(self.contract.verification_commands[0], command_id="escape", cwd="../")
        provider = TrustedLocalVerifier(self.root, replace(self.contract,
                                        verification_commands=(escaped,)))
        with self.assertRaisesRegex(ProviderError, "CWD_ESCAPE"):
            provider.run_verification("escape")

    def test_minimal_environment_does_not_inherit_parent(self):
        old = os.environ.get("LEAK")
        os.environ["LEAK"] = "secret"
        try:
            result = self.provider.run_verification("environment")
        finally:
            if old is None:
                os.environ.pop("LEAK", None)
            else:
                os.environ["LEAK"] = old
        self.assertEqual(result.stdout, b"present|none")

    def test_workspace_tracks_content_changes_and_excludes_git(self):
        request = self.local_request(["src/**"])
        before = self.provider.observe_workspace(request)
        (self.root / "src" / "tracked.txt").write_text("after\n")
        (self.root / "src" / "untracked.txt").write_text("new\n")
        after = self.provider.observe_workspace(request)
        self.assertNotEqual(before.verification_input_fingerprint,
                            after.verification_input_fingerprint)
        self.assertEqual(after.changed_paths, ("src/tracked.txt", "src/untracked.txt"))
        (self.root / ".git" / "ignored-by-provider").write_text("not business content\n")
        git_only = self.provider.observe_workspace(request)
        self.assertEqual(after.verification_input_fingerprint,
                         git_only.verification_input_fingerprint)

    def test_local_manifest_attributes_changes_since_its_origin(self):
        request = self.local_request(["src/**"])
        (self.root / "src" / "already-untracked.txt").write_text("old\n")
        before = self.provider.observe_workspace(request)
        self.assertIn("src/already-untracked.txt", before.file_manifest)
        (self.root / "src" / "tracked.txt").write_text("after\n")
        (self.root / "src" / "added-after-origin.txt").write_text("new\n")
        after = self.provider.observe_workspace(replace(request, scope_origin=before))
        self.assertEqual(after.changed_paths,
                         ("src/added-after-origin.txt", "src/tracked.txt"))
        with self.assertRaises(TypeError):
            after.file_manifest["src/forbidden.txt"] = "sha256:" + "0" * 64

    def test_manifestless_local_origin_fails_closed_before_deleted_path_is_hidden(self):
        request = self.local_request(["src/**"])
        (self.root / "src" / "tracked.txt").unlink()
        for incomplete_origin in (replace(origin(), provider="trusted-local"), origin()):
            with self.subTest(origin=incomplete_origin.provider):
                with self.assertRaisesRegex(ProviderError, "SCOPE_ORIGIN_MANIFEST_UNAVAILABLE"):
                    self.provider.observe_workspace(replace(request, scope_origin=incomplete_origin))

    def test_fingerprint_is_sorted_globally_by_posix_path(self):
        (self.root / "a").mkdir()
        (self.root / "a" / "x.txt").write_text("a\n")
        (self.root / "z.txt").write_text("z\n")
        observed = self.provider.observe_workspace(self.local_request(["**/*"]))
        expected = {relative: canonical_sha256({"content_sha256": "sha256:" + sha256((self.root / relative).read_bytes()).hexdigest(),
                                               "mode": (self.root / relative).stat().st_mode & 0o7777})
                    for relative in ("a/x.txt", "src/tracked.txt", "z.txt")}
        self.assertEqual(observed.verification_input_fingerprint,
                         canonical_sha256(expected))
        self.assertEqual(tuple(observed.file_manifest), tuple(sorted(observed.file_manifest)))

    def test_git_regular_file_and_symlink_are_excluded_from_manifest(self):
        before = self.provider.observe_workspace(self.local_request(["**/*"]))
        shutil.rmtree(self.root / ".git")
        (self.root / ".git").write_text("gitdir: elsewhere\n")
        regular = self.provider.observe_workspace(self.local_request(["**/*"]))
        self.assertEqual(before.verification_input_fingerprint,
                         regular.verification_input_fingerprint)
        self.assertNotIn(".git", regular.file_manifest)
        (self.root / ".git").unlink()
        outside_temp = TemporaryDirectory()
        self.addCleanup(outside_temp.cleanup)
        outside = Path(outside_temp.name) / "linked-git"
        outside.mkdir()
        (self.root / ".git").symlink_to(outside, target_is_directory=True)
        linked = self.provider.observe_workspace(self.local_request(["**/*"]))
        self.assertEqual(before.verification_input_fingerprint,
                         linked.verification_input_fingerprint)
        self.assertNotIn(".git", linked.file_manifest)

    def test_runtime_directory_does_not_change_business_revision(self):
        before = self.provider.observe_workspace(self.local_request(["**/*"]))
        runtime = self.root / ".unified-dev-flow"
        runtime.mkdir()
        (runtime / "events.jsonl").write_text("runtime\n")
        after = self.provider.observe_workspace(self.local_request(["**/*"]))
        self.assertEqual(before.verification_input_fingerprint,
                         after.verification_input_fingerprint)

    def test_workspace_rejects_symlink_escape(self):
        outside = self.root.parent / "provider-outside.txt"
        outside.write_text("outside\n")
        (self.root / "src" / "escape").symlink_to(outside)
        with self.assertRaisesRegex(ProviderError, "WORKSPACE_ESCAPE"):
            self.provider.observe_workspace(self.local_request())


if __name__ == "__main__":
    unittest.main()
