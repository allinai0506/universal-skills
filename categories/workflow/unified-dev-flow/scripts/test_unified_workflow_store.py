#!/usr/bin/env python3
"""Real-filesystem durability and request protocol contracts."""
from dataclasses import replace
import fcntl
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from test_unified_workflow_gate import command, evidence, workspace
from test_unified_workflow_model import valid_route, valid_task
from unified_workflow.commands import Allowed, Denied
from unified_workflow.events import IntegrityError
from unified_workflow.model import ValidationError, canonical_json
from unified_workflow.store import RunStore, VerificationResult


class CountingProvider:
    name = "mock"
    version = "1"

    def __init__(self):
        self.calls = 0
        self.observations = 0

    def observe_workspace(self, request):
        self.observations += 1
        assert request.task_contract.task_id == "task-001"
        assert request.scope_origin is not None
        return workspace()

    def run_verification(self, command_id):
        self.calls += 1
        return VerificationResult(started_at="2026-09-11T00:00:00Z",
            ended_at="2026-09-11T00:00:01Z", exit_code=0, timed_out=False,
            output_truncated=False, stdout=b"ok", stderr=b"", stdout_bytes=2,
            stderr_bytes=0, stdout_sha256=sha256(b"ok").hexdigest(),
            stderr_sha256=sha256(b"").hexdigest())


def crash_worker(root, cmd, phase):
    if phase == "committed":
        real_sync = os.fsync
        def sync_then_die(fd):
            real_sync(fd)
            path = Path(root) / ".unified-dev-flow/runs/work-1/events.jsonl"
            if os.fstat(fd).st_ino == path.stat().st_ino:
                last = json.loads(path.read_text().splitlines()[-1])
                if last["request_id"] == cmd.request_id and any(
                        item["event_type"] == "REQUEST_RESOLVED" for item in last["events"]):
                    os._exit(23)
        os.fsync = sync_then_die
    class CrashProvider(CountingProvider):
        def observe_workspace(self, request):
            if phase == "reserved" or phase == "blobs" and self.observations == 2:
                os._exit(23)
            return super().observe_workspace(request)

        def run_verification(self, command_id):
            with open(Path(root) / "provider-called", "ab") as stream:
                stream.write(b"called\n")
            if phase == "provider":
                os._exit(23)
            return super().run_verification(command_id)
    RunStore(Path(root), "work-1").execute_verification(cmd, CrashProvider())


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = RunStore(self.root, "work-1")
        self.send("INIT_RUN", route=valid_route())
        self.send("ADD_TASK", "task-001", task=valid_task())
        self.send("READY_TASK", "task-001")
        self.send("START_TASK", "task-001", facts=workspace())

    def cmd(self, kind, task_id=None, request_id=None, **payload):
        return replace(command(kind, task_id, **payload),
                       request_id=request_id or "req-" + str(self.store.sequence + 1),
                       expected_sequence=self.store.sequence)

    def send(self, kind, task_id=None, facts=None, **payload):
        result = self.store.execute(self.cmd(kind, task_id, **payload), facts)
        self.assertIsInstance(result.outcome, Allowed)
        return result

    def verify_command(self, request_id="verify-1"):
        return self.cmd("RECORD_VERIFICATION", "task-001", request_id=request_id,
                        command_id=valid_task()["verification_commands"][0]["command_id"])

    def test_retry_returns_prior_outcome_without_calling_provider_twice(self):
        provider = CountingProvider()
        cmd = self.verify_command()
        first = self.store.execute_verification(cmd, provider)
        second = RunStore(self.root, "work-1").execute_verification(cmd, provider)
        self.assertIsInstance(first.outcome, Allowed)
        self.assertEqual(first.outcome, second.outcome)
        self.assertEqual(first.state, second.state)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(provider.observations, 3)
        self.assertEqual(second.state.requests[cmd.request_id].outcome, "success")

    def test_retry_syncs_readable_resolution_after_transient_final_fsync_failure(self):
        cmd = self.verify_command()
        provider = CountingProvider()
        real_sync = os.fsync
        final_attempts = []
        synced_after_retry = []
        def sync(fd):
            info = os.fstat(fd)
            if info.st_ino == self.store.events_path.stat().st_ino:
                batch = json.loads(self.store.events_path.read_text().splitlines()[-1])
                if batch["request_id"] == cmd.request_id and batch["events"][-1]["event_type"] == "REQUEST_RESOLVED":
                    final_attempts.append(fd)
                    if len(final_attempts) == 1:
                        raise OSError("transient event fsync failure")
                    synced_after_retry.append("events")
            elif info.st_ino == self.store.run_dir.stat().st_ino and len(final_attempts) > 1:
                synced_after_retry.append("directory")
            return real_sync(fd)
        with patch("unified_workflow.store.os.fsync", side_effect=sync):
            with self.assertRaisesRegex(OSError, "transient event fsync failure"):
                self.store.execute_verification(cmd, provider)
            retry = RunStore(self.root, "work-1").execute_verification(cmd, provider)
        self.assertIsInstance(retry.outcome, Allowed)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(len(final_attempts), 2)
        self.assertEqual(synced_after_retry, ["events", "directory"])

    def test_retry_fails_closed_while_final_event_fsync_keeps_failing(self):
        cmd = self.verify_command()
        provider = CountingProvider()
        real_sync = os.fsync
        failures = []
        def sync(fd):
            if os.fstat(fd).st_ino == self.store.events_path.stat().st_ino:
                batch = json.loads(self.store.events_path.read_text().splitlines()[-1])
                if batch["request_id"] == cmd.request_id and batch["events"][-1]["event_type"] == "REQUEST_RESOLVED":
                    failures.append(fd)
                    raise OSError("persistent event fsync failure")
            return real_sync(fd)
        with patch("unified_workflow.store.os.fsync", side_effect=sync):
            for _ in range(2):
                with self.assertRaisesRegex(OSError, "persistent event fsync failure"):
                    self.store.execute_verification(cmd, provider)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(len(failures), 2)

    def test_generic_execute_rejects_supplied_verification_evidence_stably(self):
        state = self.store.load()
        cmd = self.cmd("RECORD_VERIFICATION", "task-001", evidence=evidence(state))
        result = self.store.execute(cmd, workspace())
        self.assertIsInstance(result.outcome, Denied)
        self.assertEqual(result.outcome.reason_code, "INVALID_CONTRACT")
        self.assertEqual(result.state.tasks["task-001"].verifications, ())
        sequence = self.store.sequence
        self.assertEqual(self.store.execute(cmd, workspace()).outcome, result.outcome)
        self.assertEqual(self.store.sequence, sequence)

    def test_generic_execute_rejects_even_a_previously_executed_verification(self):
        cmd = self.verify_command()
        self.store.execute_verification(cmd, CountingProvider())
        before = self.store.events_path.read_bytes()
        result = self.store.execute(cmd)
        self.assertEqual(result.outcome.reason_code, "INVALID_CONTRACT")
        self.assertEqual(self.store.events_path.read_bytes(), before)

    def test_retry_reestablishes_directory_durability_after_final_directory_sync_failure(self):
        cmd = self.verify_command()
        provider = CountingProvider()
        real_sync = os.fsync
        directory_attempts = []
        sync_order = []
        def sync(fd):
            batch = json.loads(self.store.events_path.read_text().splitlines()[-1])
            if batch["request_id"] == cmd.request_id and batch["events"][-1]["event_type"] == "REQUEST_RESOLVED":
                inode = os.fstat(fd).st_ino
                if inode == self.store.events_path.stat().st_ino:
                    sync_order.append("events")
                elif inode == self.store.run_dir.stat().st_ino:
                    directory_attempts.append(fd)
                    sync_order.append("directory")
                    if len(directory_attempts) == 1:
                        raise OSError("transient directory fsync failure")
            return real_sync(fd)
        with patch("unified_workflow.store.os.fsync", side_effect=sync):
            with self.assertRaisesRegex(OSError, "transient directory fsync failure"):
                self.store.execute_verification(cmd, provider)
            sync_order.clear()
            retry = self.store.execute_verification(cmd, provider)
        self.assertIsInstance(retry.outcome, Allowed)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(sync_order[-2:], ["events", "directory"])

    def test_constructing_store_does_not_create_runtime(self):
        with TemporaryDirectory() as root:
            store = RunStore(Path(root), "work-1")
            self.assertEqual(store.sequence, 0)
            self.assertFalse((Path(root) / ".unified-dev-flow").exists())

    def test_patch_init_denial_does_not_create_control_directory(self):
        with TemporaryDirectory() as root:
            store = RunStore(Path(root), "work-1")
            route = valid_route()
            route["delivery_target"] = "patch"
            result = store.execute(command("INIT_RUN", route=route))
            self.assertEqual(result.outcome.reason_code, "RUNTIME_NOT_AUTHORIZED")
            self.assertEqual(result.state.status, "new")
            self.assertFalse((Path(root) / ".unified-dev-flow").exists())

    def test_patch_init_reusing_original_request_id_reports_idempotency_conflict(self):
        route = valid_route()
        route["delivery_target"] = "patch"
        cmd = replace(command("INIT_RUN", route=route), request_id="req-1")
        before = self.store.events_path.read_bytes()
        result = self.store.execute(cmd)
        self.assertEqual(result.outcome.reason_code, "IDEMPOTENCY_CONFLICT")
        self.assertEqual(result.state.status, "active")
        self.assertIn("task-001", result.state.tasks)
        self.assertEqual(self.store.events_path.read_bytes(), before)

    def test_patch_init_on_existing_run_returns_persisted_state(self):
        route = valid_route()
        route["delivery_target"] = "patch"
        result = self.store.execute(self.cmd("INIT_RUN", route=route))
        self.assertEqual(result.outcome.reason_code, "INVALID_TRANSITION")
        self.assertEqual(result.state.status, "active")
        self.assertEqual(result.state.tasks["task-001"].status, "running")

    def test_patch_init_cannot_bypass_corrupt_existing_log(self):
        route = valid_route()
        route["delivery_target"] = "patch"
        self.store.events_path.write_bytes(b"unterminated")
        with self.assertRaisesRegex(IntegrityError, "EVENT_JSON_CORRUPT"):
            self.store.execute(self.cmd("INIT_RUN", route=route))
        self.assertEqual(self.store.events_path.read_bytes(), b"unterminated")

    def test_patch_init_rejects_symlinked_control_instead_of_treating_it_as_absent(self):
        with TemporaryDirectory() as root:
            root = Path(root)
            target = root / "missing-target"
            (root / ".unified-dev-flow").symlink_to(target, target_is_directory=True)
            route = valid_route()
            route["delivery_target"] = "patch"
            with self.assertRaisesRegex(ValidationError, "UNSAFE_CONTROL_PATH"):
                RunStore(root, "work-1").execute(command("INIT_RUN", route=route))
            self.assertFalse(target.exists())

    def test_patch_init_observes_runtime_created_during_gate_preflight(self):
        with TemporaryDirectory() as root:
            root = Path(root)
            store = RunStore(root, "work-1")
            route = valid_route()
            route["delivery_target"] = "patch"
            from unified_workflow.gate_kernel import decide as real_decide
            def preflight(state, cmd, facts):
                result = real_decide(state, cmd, facts)
                if cmd.request_id != "creator":
                    other = RunStore(root, "work-1")
                    other.execute(replace(command("INIT_RUN", route=valid_route()), request_id="creator"))
                return result
            with patch("unified_workflow.store.decide", side_effect=preflight):
                result = store.execute(command("INIT_RUN", route=route))
            self.assertEqual(result.outcome.reason_code, "EXPECTED_SEQUENCE_MISMATCH")
            self.assertEqual(result.state.status, "active")

    def test_patch_init_for_absent_sibling_run_creates_no_target_runtime(self):
        route = valid_route()
        route["delivery_target"] = "patch"
        before = self.store.events_path.read_bytes()
        target = RunStore(self.root, "work-2")
        result = target.execute(replace(command("INIT_RUN", route=route), work_id="work-2"))
        self.assertEqual(result.outcome.reason_code, "RUNTIME_NOT_AUTHORIZED")
        self.assertEqual(result.state.status, "new")
        self.assertFalse(target.run_dir.exists())
        self.assertEqual(self.store.events_path.read_bytes(), before)

    def test_patch_init_rejects_unsafe_target_run_components(self):
        for kind in ("symlink", "dangling-symlink", "file", "hardlink"):
            with self.subTest(kind=kind), TemporaryDirectory() as root:
                root = Path(root)
                control = root / ".unified-dev-flow/runs"
                control.mkdir(parents=True)
                target = control / "work-2"
                sentinel = root / "sentinel"
                sentinel.write_bytes(b"untouched")
                if kind == "symlink":
                    target.symlink_to(root, target_is_directory=True)
                elif kind == "dangling-symlink":
                    target.symlink_to(root / "absent", target_is_directory=True)
                elif kind == "file":
                    target.write_bytes(b"not a directory")
                else:
                    os.link(sentinel, target)
                route = valid_route()
                route["delivery_target"] = "patch"
                with self.assertRaisesRegex(ValidationError, "UNSAFE_CONTROL_PATH"):
                    RunStore(root, "work-2").execute(
                        replace(command("INIT_RUN", route=route), work_id="work-2"))
                self.assertEqual(sentinel.read_bytes(), b"untouched")
                self.assertFalse((root / "absent").exists())

    def test_patch_init_observes_target_created_between_checks_with_sibling_present(self):
        target = RunStore(self.root, "work-2")
        route = valid_route()
        route["delivery_target"] = "patch"
        from unified_workflow.gate_kernel import decide as real_decide
        def preflight(state, cmd, facts):
            result = real_decide(state, cmd, facts)
            if cmd.request_id != "creator":
                other = RunStore(self.root, "work-2")
                created = other.execute(replace(command("INIT_RUN", route=valid_route()),
                                               request_id="creator", work_id="work-2"))
                self.assertIsInstance(created.outcome, Allowed)
            return result
        with patch("unified_workflow.store.decide", side_effect=preflight):
            result = target.execute(replace(command("INIT_RUN", route=route), work_id="work-2"))
        self.assertEqual(result.outcome.reason_code, "EXPECTED_SEQUENCE_MISMATCH")
        self.assertEqual(result.state.status, "active")
        self.assertIn("creator", result.state.requests)

    def test_process_crashes_leave_in_doubt_without_rerunning_provider(self):
        for phase in ("reserved", "provider", "blobs"):
            with self.subTest(phase=phase):
                cmd = self.verify_command("crash-" + phase)
                child = multiprocessing.get_context("fork").Process(
                    target=crash_worker, args=(self.root, cmd, phase))
                child.start()
                child.join(10)
                self.assertEqual(child.exitcode, 23)
                provider = CountingProvider()
                result = self.store.execute_verification(cmd, provider)
                self.assertEqual(result.outcome.reason_code, "REQUEST_IN_DOUBT")
                self.assertEqual(result.state.requests[cmd.request_id].status, "in_doubt")
                self.assertEqual(provider.calls, 0)
                self.assertEqual(provider.observations, 0)
        self.assertEqual((self.root / "provider-called").read_text(), "called\ncalled\n")

    def test_explicit_resolution_is_audited_and_retry_is_stable(self):
        cmd = self.verify_command()
        with patch.object(CountingProvider, "run_verification", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.store.execute_verification(cmd, CountingProvider())
        result = self.store.resolve_request(cmd.request_id, "abandoned",
            {"type": "human", "id": "operator"}, "Inspected child process; abandoned attempt.")
        self.assertEqual(result.status, "abandoned")
        self.assertEqual(self.store.execute_verification(cmd, CountingProvider()).outcome, result.outcome)
        last = json.loads(self.store.events_path.read_text().splitlines()[-1])
        self.assertEqual(last["actor"]["id"], "operator")
        self.assertIn("Inspected child", last["events"][-1]["payload"]["result_summary"]["note"])

    def test_death_after_final_fsync_replays_success_without_provider(self):
        cmd = self.verify_command()
        child = multiprocessing.get_context("fork").Process(
            target=crash_worker, args=(self.root, cmd, "committed"))
        child.start()
        child.join(10)
        self.assertEqual(child.exitcode, 23)
        provider = CountingProvider()
        result = self.store.execute_verification(cmd, provider)
        self.assertIsInstance(result.outcome, Allowed)
        self.assertEqual(provider.calls, 0)
        self.assertEqual(provider.observations, 0)

    def test_reservation_is_fsynced_before_first_provider_observation(self):
        synced_events = []
        original = os.fsync
        def sync(fd):
            original(fd)
            if os.fstat(fd).st_ino == self.store.events_path.stat().st_ino:
                synced_events.append(json.loads(self.store.events_path.read_text().splitlines()[-1]))
        provider = CountingProvider()
        observe = provider.observe_workspace
        def observed(request):
            self.assertEqual(synced_events[-1]["events"][-1]["event_type"], "REQUEST_RESERVED")
            return observe(request)
        provider.observe_workspace = observed
        with patch("unified_workflow.store.os.fsync", side_effect=sync):
            result = self.store.execute_verification(self.verify_command(), provider)
        self.assertIsInstance(result.outcome, Allowed)
        self.assertEqual(len(synced_events), 2)
        self.assertEqual(synced_events[-1]["events"][-1]["event_type"], "REQUEST_RESOLVED")

    def test_resolution_event_ids_address_domain_events_in_the_batch(self):
        for line in self.store.events_path.read_text().splitlines():
            batch = json.loads(line)
            resolution = batch["events"][-1]["payload"]
            for event_id in resolution["event_ids"]:
                prefix, index = event_id.rsplit(".", 1)
                self.assertEqual(prefix, batch["batch_id"])
                self.assertNotIn(batch["events"][int(index)]["event_type"],
                                 ("REQUEST_RESERVED", "REQUEST_RESOLVED"))

    def test_truncated_stream_blob_digest_is_for_retained_bytes(self):
        provider = CountingProvider()
        output = replace(provider.run_verification("unit"), stdout_bytes=4,
                         stdout_sha256=sha256(b"okay").hexdigest(), output_truncated=True)
        provider.run_verification = lambda command_id: output
        result = self.store.execute_verification(self.verify_command(), provider)
        self.assertEqual(result.outcome.reason_code, "EVIDENCE_MISSING")
        self.assertEqual(self.store.load(), result.state)
        self.assertEqual(self.store.diagnostics, ())

    def test_scope_denial_persists_verification_and_scope_fact_atomically(self):
        provider = CountingProvider()
        provider.observe_workspace = lambda request: workspace(paths=["outside.txt"])
        result = self.store.execute_verification(self.verify_command(), provider)
        self.assertEqual(result.outcome.reason_code, "SCOPE_VIOLATION")
        batch = json.loads(self.store.events_path.read_text().splitlines()[-1])
        self.assertEqual([item["event_type"] for item in batch["events"]],
            ["VERIFICATION_RECORDED", "SCOPE_VIOLATION", "REQUEST_RESOLVED"])
        self.assertEqual(self.store.load(), result.state)

    def test_failed_blob_rename_leaves_reservation_and_no_temporary_file(self):
        cmd = self.verify_command()
        with patch("unified_workflow.store.os.replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.store.execute_verification(cmd, CountingProvider())
        self.assertFalse(list(self.store.run_dir.rglob("*.tmp")))
        result = self.store.execute_verification(cmd, CountingProvider())
        self.assertEqual(result.outcome.reason_code, "REQUEST_IN_DOUBT")

    def test_provider_failure_is_resolved_and_stable(self):
        cmd = self.verify_command()
        provider = CountingProvider()
        with patch.object(provider, "run_verification", side_effect=RuntimeError("offline")):
            first = self.store.execute_verification(cmd, provider)
        second = self.store.execute_verification(cmd, provider)
        self.assertEqual(first.status, "provider_failure")
        self.assertEqual(first.outcome, second.outcome)
        self.assertEqual(second.state.requests[cmd.request_id].outcome, "provider_failure")

    def test_writer_lock_busy_and_held_during_provider(self):
        with self.store.lock_path.open("rb") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.store.execute(self.cmd("CANCEL_RUN"))
            self.assertEqual(result.outcome.reason_code, "LOCK_BUSY")
        provider = CountingProvider()
        original = provider.run_verification
        def probe(command_id):
            other = RunStore(self.root, "work-1")
            result = other.execute(self.cmd("CANCEL_RUN"))
            self.assertEqual(result.outcome.reason_code, "LOCK_BUSY")
            return original(command_id)
        provider.run_verification = probe
        self.assertIsInstance(self.store.execute_verification(self.verify_command(), provider).outcome, Allowed)

    def test_expected_sequence_and_idempotency_conflict_do_not_append(self):
        stale = self.cmd("CANCEL_RUN", request_id="stale")
        current = self.cmd("REPORT_TASK", "task-001", report={"summary": "work"},
                           workspace_revision=workspace().to_dict())
        self.store.execute(current, workspace())
        before = self.store.events_path.read_bytes()
        self.assertEqual(self.store.execute(stale).outcome.reason_code, "EXPECTED_SEQUENCE_MISMATCH")
        conflict = replace(current, payload={})
        self.assertEqual(self.store.execute(conflict).outcome.reason_code, "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.store.events_path.read_bytes(), before)

    def test_pure_denial_is_durable_and_has_no_separate_reservation(self):
        before = self.store.sequence
        cmd = self.cmd("ACCEPT_TASK", "task-001")
        result = self.store.execute(cmd)
        self.assertIsInstance(result.outcome, Denied)
        self.assertEqual(self.store.sequence, before + 1)
        self.assertEqual(result.outcome, self.store.execute(cmd).outcome)
        self.assertEqual(result.state.requests[cmd.request_id].status, "resolved")

    def test_invalid_verification_never_runs_provider(self):
        for cmd in (replace(self.verify_command(), payload={"command_id": "unknown"}),
                    self.cmd("CANCEL_RUN")):
            with self.subTest(command=cmd):
                provider = CountingProvider()
                result = self.store.execute_verification(cmd, provider)
                self.assertIsInstance(result.outcome, Denied)
                self.assertEqual(provider.calls, 0)
                self.assertEqual(provider.observations, 0)

    def test_missing_and_corrupt_optional_blobs_warn_without_changing_replay(self):
        state = self.store.execute_verification(self.verify_command(), CountingProvider()).state
        item = state.tasks["task-001"].verifications[-1]["evidence"]
        blob = self.store.run_dir / item["stdout_blob_ref"]
        blob.write_bytes(b"bad")
        self.assertEqual(self.store.load(), state)
        self.assertIn("DIAGNOSTIC_BLOB_DIGEST_MISMATCH", self.store.diagnostics)
        blob.unlink()
        self.assertEqual(self.store.load(), state)
        self.assertIn("MISSING_DIAGNOSTIC_BLOB", self.store.diagnostics)

    def test_blob_publication_syncs_temp_before_rename_and_directory_after(self):
        actions = []
        real_sync, real_replace = os.fsync, os.replace
        def sync(fd):
            actions.append("dir" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
            return real_sync(fd)
        def rename(*args, **kwargs):
            actions.append("rename")
            return real_replace(*args, **kwargs)
        with patch("unified_workflow.store.os.fsync", side_effect=sync), patch(
                "unified_workflow.store.os.replace", side_effect=rename):
            ref = self.store.publish_blob(b"diagnostic")
        self.assertEqual(ref.sha256, "sha256:" + sha256(b"diagnostic").hexdigest())
        self.assertEqual((self.store.run_dir / ref.path).read_bytes(), b"diagnostic")
        self.assertLess(actions.index("file"), actions.index("rename"))
        self.assertIn("dir", actions[actions.index("rename") + 1:])
        self.assertFalse(list(self.store.run_dir.rglob("*.tmp")))

    def test_corruption_fails_closed_without_repair(self):
        original = self.store.events_path.read_bytes()
        raw = json.loads(original.splitlines()[-1])
        corruptions = [original[:-1], original + b"{\n", original + b"\xff\n"]
        for field, value in (("batch_hash", "sha256:" + "0" * 64), ("schema_version", 999),
                             ("sequence", 99), ("unexpected", True)):
            bad = {**raw, field: value}
            corruptions.append(b"\n".join(original.splitlines()[:-1]) + b"\n" +
                               json.dumps(bad).encode() + b"\n")
        for bad in corruptions:
            with self.subTest(tail=bad[-50:]):
                self.store.events_path.write_bytes(bad)
                with self.assertRaises((IntegrityError, ValidationError)):
                    self.store.load()
                with self.assertRaises((IntegrityError, ValidationError)):
                    self.store.execute(self.cmd("CANCEL_RUN"))
                self.assertEqual(self.store.events_path.read_bytes(), bad)
        self.store.events_path.write_bytes(original)

    def test_private_modes_canonical_batches_and_no_snapshots(self):
        self.store.publish_blob(b"data")
        control = self.root / ".unified-dev-flow"
        for path in (control, *control.rglob("*")):
            expected = 0o700 if path.is_dir() else 0o600
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), expected, str(path))
            self.assertNotIn(path.name, ("run.json", "tasks.json", "state.json"))
        for line in self.store.events_path.read_text().splitlines():
            self.assertEqual(line, canonical_json(json.loads(line)))
        self.assertFalse((self.root / ".omc").exists())
        self.assertFalse((self.root / ".superpowers").exists())

    def test_symlinked_control_components_and_files_are_rejected(self):
        for relative in (".unified-dev-flow", ".unified-dev-flow/runs",
                         ".unified-dev-flow/runs/work-1", ".unified-dev-flow/runs/work-1/blobs",
                         ".unified-dev-flow/runs/work-1/events.jsonl",
                         ".unified-dev-flow/runs/work-1/run.lock"):
            with self.subTest(path=relative), TemporaryDirectory() as temp:
                root = Path(temp)
                outside = root / "outside"
                outside.mkdir()
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(outside, target_is_directory=True)
                with self.assertRaises(ValidationError):
                    RunStore(root, "work-1").load()
                self.assertEqual(list(outside.iterdir()), [])

    def test_late_symlink_and_invalid_work_id_rejected(self):
        with self.assertRaises(ValidationError):
            RunStore(self.root, "../escape")
        self.store.events_path.unlink()
        sentinel = self.root / "sentinel"
        sentinel.write_text("do not touch")
        self.store.events_path.symlink_to(sentinel)
        with self.assertRaises(ValidationError):
            self.store.execute(self.cmd("CANCEL_RUN"))
        self.assertEqual(sentinel.read_text(), "do not touch")


if __name__ == "__main__":
    unittest.main()
