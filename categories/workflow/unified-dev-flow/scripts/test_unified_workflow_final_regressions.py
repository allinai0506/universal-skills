#!/usr/bin/env python3
"""Integration regressions from the phase-two final contract review."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from test_unified_workflow_cli import CLIProject
from test_unified_workflow_gate import (apply, command, delivery, evidence, review,
                                       task, workspace)
from test_unified_workflow_model import valid_route, valid_task
from test_unified_workflow_providers import task_dict
from test_unified_workflow_store import CountingProvider
from unified_workflow.commands import Allowed, Denied
from unified_workflow.events import DomainEvent, EventBatch, IntegrityError, ZERO_HASH
from unified_workflow.gate_kernel import decide, fresh_evidence, fresh_review
from unified_workflow.model import TaskContract, ValidationError, WorkspaceRevision, canonical_sha256
from unified_workflow.providers import ProviderError, TrustedLocalVerifier
from unified_workflow.reducer import replay
from unified_workflow.store import ObserveRequest, RunStore


class WorkspaceObservationRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "alpha").mkdir()
        (self.root / "alpha/a.txt").write_text("alpha")
        (self.root / "outside.txt").write_text("outside")
        self.contract = TaskContract.from_dict(task_dict([], ("alpha/**",)))
        self.provider = TrustedLocalVerifier(self.root, self.contract)
        self.empty = WorkspaceRevision.from_dict(dict(schema_version=1, provider="trusted-local",
            revision_id="empty", verification_input_fingerprint=canonical_sha256({}),
            changed_paths=[], observed_at="2026-09-11T00:00:00Z", file_manifest={}))

    def observe(self, origin=None, inputs=None):
        contract = self.contract if inputs is None else replace(self.contract, verification_inputs=tuple(inputs))
        return self.provider.observe_workspace(ObserveRequest(contract, origin or self.empty))

    def test_changes_outside_verification_inputs_still_change_revision_and_scope(self):
        for action in ("create", "modify", "delete"):
            with self.subTest(action=action):
                target = self.root / ("new.txt" if action == "create" else "outside.txt")
                if action != "create":
                    target.write_text("before")
                before = self.observe()
                if action == "delete":
                    target.unlink()
                else:
                    target.write_text("changed")
                after = self.observe(before)
                self.assertIn(target.name, after.changed_paths)
                self.assertNotEqual(before.revision_id, after.revision_id)
                self.assertEqual(before.verification_input_fingerprint, after.verification_input_fingerprint)

    def test_whole_workspace_identity_is_independent_of_selected_inputs(self):
        alpha = self.observe(inputs=["alpha/**"])
        other = self.observe(inputs=["outside.txt"])
        self.assertEqual(alpha.revision_id, other.revision_id)
        self.assertNotEqual(alpha.verification_input_fingerprint, other.verification_input_fingerprint)

    def test_file_mode_changes_obey_scope_and_input_selection(self):
        (self.root / "outside.txt").chmod(0o644)
        before = self.observe()
        (self.root / "outside.txt").chmod(0o755)
        changed = self.observe(before)
        self.assertIn("outside.txt", changed.changed_paths)
        self.assertNotEqual(before.revision_id, changed.revision_id)
        self.assertEqual(before.verification_input_fingerprint, changed.verification_input_fingerprint)
        selected = self.observe(inputs=["outside.txt"])
        (self.root / "outside.txt").chmod(0o644)
        self.assertNotEqual(selected.verification_input_fingerprint,
                            self.observe(selected, ["outside.txt"]).verification_input_fingerprint)

    def test_file_symlink_observes_resolved_content_and_retarget(self):
        link = self.root / "link.txt"
        link.symlink_to("outside.txt")
        before = self.observe(inputs=["link.txt"])
        (self.root / "outside.txt").write_text("changed")
        changed = self.observe(before, ["link.txt"])
        self.assertNotEqual(before.verification_input_fingerprint, changed.verification_input_fingerprint)
        self.assertIn("link.txt", changed.changed_paths)
        (self.root / "equal.txt").write_text("changed")
        before_retarget = self.observe(inputs=["link.txt"])
        link.unlink()
        link.symlink_to("equal.txt")
        retargeted = self.observe(before_retarget, ["link.txt"])
        self.assertNotEqual(before_retarget.verification_input_fingerprint, retargeted.verification_input_fingerprint)

    def test_directory_symlink_observes_tree_and_retarget_with_equal_contents(self):
        (self.root / "alias").symlink_to("alpha", target_is_directory=True)
        before = self.observe(inputs=["alias/*.txt"])
        (self.root / "alpha/a.txt").write_text("new alpha")
        changed = self.observe(before, ["alias/*.txt"])
        self.assertNotEqual(before.verification_input_fingerprint, changed.verification_input_fingerprint)
        self.assertIn("alias/a.txt", changed.changed_paths)
        (self.root / "beta").mkdir()
        (self.root / "beta/a.txt").write_text("new alpha")
        baseline = self.observe(inputs=["alias/*.txt"])
        (self.root / "alias").unlink()
        (self.root / "alias").symlink_to("beta", target_is_directory=True)
        retargeted = self.observe(baseline, ["alias/*.txt"])
        self.assertNotEqual(baseline.verification_input_fingerprint, retargeted.verification_input_fingerprint)

    def test_directory_link_input_selects_content_without_unselected_siblings(self):
        (self.root / "alias").symlink_to("alpha", target_is_directory=True)
        (self.root / "alpha/nested").mkdir()
        (self.root / "alpha/nested/a.txt").write_text("nested")
        before = self.observe(inputs=["alias/*.txt"])
        whole_tree = self.observe(inputs=["alias"])
        (self.root / "alpha/nested/a.txt").write_text("unselected nested change")
        after = self.observe(before, ["alias/*.txt"])
        after_tree = self.observe(whole_tree, ["alias"])
        self.assertEqual(before.verification_input_fingerprint, after.verification_input_fingerprint)
        self.assertNotEqual(whole_tree.verification_input_fingerprint, after_tree.verification_input_fingerprint)
        self.assertNotEqual(before.revision_id, after.revision_id)

    def test_symlink_into_control_state_is_rejected(self):
        (self.root / ".unified-dev-flow").mkdir()
        (self.root / ".unified-dev-flow/log").write_text("state")
        (self.root / "alias").symlink_to(".unified-dev-flow", target_is_directory=True)
        with self.assertRaisesRegex(ProviderError, "WORKSPACE_CONTROL_PATH"):
            self.observe()

    def test_symlink_cycle_fails_closed(self):
        (self.root / "alpha/loop").symlink_to(".", target_is_directory=True)
        with self.assertRaisesRegex(ProviderError, "WORKSPACE_CYCLE"):
            self.observe()


class FreshnessRegressions(unittest.TestCase):
    def test_delivery_revision_or_provider_drift_cannot_complete_with_same_inputs(self):
        state = task(status="accepted")
        state = apply(state, decide(state, delivery(state), workspace()))
        for observed in (replace(workspace(), revision_id="new-workspace"),
                         replace(workspace(), provider="other-provider")):
            with self.subTest(observed=observed):
                result = decide(state, command("COMPLETE_RUN"), observed)
                self.assertIsInstance(result.outcome, Denied)
                self.assertEqual(result.outcome.reason_code, "EVIDENCE_STALE")
                self.assertFalse(any(event.event_type == "RUN_COMPLETED" for event in result.events))
                self.assertTrue(state.tasks["task-001"].currently_satisfied)

    def test_non_input_workspace_drift_preserves_fresh_evidence_and_review(self):
        state = task(status="waiting_review")
        observed = replace(workspace(), revision_id="other-files-changed", changed_paths=("src/other.txt",))
        self.assertEqual(len(fresh_evidence(state.tasks["task-001"], observed)), 1)
        from unified_workflow.model import ReviewAssertion
        self.assertTrue(fresh_review(state.tasks["task-001"], ReviewAssertion.from_dict(review(state)), observed))

    def test_recording_verification_still_requires_coherent_commit_revision(self):
        state = task(status="running")
        observed = replace(workspace(), revision_id="changed-during-commit")
        result = decide(state, command("RECORD_VERIFICATION", "task-001", evidence=evidence(state)), observed)
        self.assertEqual(result.outcome.reason_code, "EVIDENCE_STALE")
        self.assertFalse(result.events[0].payload["success"])


class AuditAndRequestRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = RunStore(self.root, "work-1")

    def send(self, kind, task_id=None, **payload):
        cmd = replace(command(kind, task_id, **payload), expected_sequence=self.store.sequence,
                      request_id="request-" + str(self.store.sequence + 1))
        return self.store.execute(cmd, workspace())

    def start(self):
        self.send("INIT_RUN", route=valid_route())
        self.send("ADD_TASK", "task-001", task=valid_task())
        self.send("READY_TASK", "task-001")
        self.send("START_TASK", "task-001")

    def verify(self):
        return replace(command("RECORD_VERIFICATION", "task-001", command_id="unit"),
                       expected_sequence=self.store.sequence, request_id="verify")

    def test_pure_commands_resolve_without_any_reservation_event(self):
        self.start()
        self.send("ACCEPT_TASK", "task-001")
        batches = [json.loads(line) for line in self.store.events_path.read_text().splitlines()]
        self.assertTrue(all(batch["events"][-1]["event_type"] == "REQUEST_RESOLVED" for batch in batches))
        self.assertFalse(any(event["event_type"] == "REQUEST_RESERVED"
                             for batch in batches for event in batch["events"]))
        self.assertTrue(all(request.reservation_sequence is None for request in self.store.load().requests.values()))

    def test_unexpected_provider_bug_propagates_and_retains_in_doubt(self):
        self.start()
        cmd = self.verify()
        provider = CountingProvider()
        with patch.object(provider, "run_verification", side_effect=TypeError("internal defect")):
            with self.assertRaisesRegex(TypeError, "internal defect"):
                self.store.execute_verification(cmd, provider)
        self.assertEqual(self.store.load().requests[cmd.request_id].status, "in_doubt")
        self.assertEqual(self.store.execute_verification(cmd, provider).outcome.reason_code, "REQUEST_IN_DOUBT")

    def test_expected_provider_error_has_stable_resolved_outcome(self):
        self.start()
        cmd = self.verify()
        provider = CountingProvider()
        with patch.object(provider, "run_verification", side_effect=ProviderError("OFFLINE", "Unavailable")):
            first = self.store.execute_verification(cmd, provider)
        self.assertEqual(first.status, "provider_failure")
        self.assertEqual(self.store.execute_verification(cmd, provider).outcome, first.outcome)

    def test_evidence_assembly_programming_bug_is_not_provider_failure(self):
        self.start()
        cmd = self.verify()
        with patch("unified_workflow.store.EvidenceRecord.from_dict", side_effect=AssertionError("assembly defect")):
            with self.assertRaisesRegex(AssertionError, "assembly defect"):
                self.store.execute_verification(cmd, CountingProvider())
        self.assertEqual(self.store.load().requests[cmd.request_id].status, "in_doubt")

    def test_pure_request_cannot_be_reserved_as_in_doubt(self):
        with self.assertRaises(ValidationError):
            DomainEvent("REQUEST_RESERVED", dict(request_id="pure", request_sha256=canonical_sha256("pure"),
                        command_type="START_TASK", reservation_sequence=1))

    def test_replay_rejects_lifecycle_identity_that_disagrees_with_batch(self):
        reserved = DomainEvent("REQUEST_RESERVED", dict(request_id="inner", request_sha256=canonical_sha256("inner"),
                               command_type="RECORD_VERIFICATION", reservation_sequence=1))
        batch = EventBatch.create(sequence=1, batch_id="batch", request_id="outer",
            request_sha256=canonical_sha256("outer"), work_id="work-1", occurred_at="2026-09-11T00:00:00Z",
            actor={"type": "test", "id": "local"}, previous_hash=ZERO_HASH, events=[reserved])
        with self.assertRaisesRegex(IntegrityError, "REQUEST_CONFLICT"):
            replay([batch])

    def test_goal_route_hash_and_batch_head_are_replayed_in_audit_view(self):
        result = self.send("INIT_RUN", goal="Deliver the specified kernel", route=valid_route())
        self.assertIsInstance(result.outcome, Allowed)
        self.send("ADD_TASK", "task-001", task=valid_task())
        batches = [EventBatch.from_dict(json.loads(line)) for line in self.store.events_path.read_text().splitlines()]
        state = replay(batches)
        self.assertEqual(state.goal, "Deliver the specified kernel")
        self.assertEqual(state.route_contract.to_dict(), valid_route())
        self.assertEqual(state.route_contract_sha256, canonical_sha256(valid_route()))
        self.assertEqual(state.latest_sequence, batches[-1].sequence)
        self.assertEqual(state.latest_hash, batches[-1].batch_hash)
        self.assertEqual(state.created_at, batches[0].occurred_at)
        self.assertEqual(state.updated_at, batches[-1].occurred_at)
        self.assertEqual(dict(state.review_rounds_by_task), {"task-001": 0})
        self.assertEqual(state.blockers, ())
        self.assertEqual(state, self.store.load())

    def test_reducer_resolves_pure_request_and_rejects_conflicting_identity(self):
        payload = dict(request_id="pure", request_sha256=canonical_sha256("pure"),
            command_type="INIT_RUN", expected_sequence=0, outcome="success", reason_code=None,
            result_summary={"outcome": {"kind": "allowed", "result": {}}}, event_ids=[])
        resolved = DomainEvent("REQUEST_RESOLVED", payload)
        batch = EventBatch.create(sequence=1, batch_id="pure-batch", request_id="pure",
            request_sha256=payload["request_sha256"], work_id="work-1", occurred_at="2026-09-11T00:00:00Z",
            actor={"type": "test", "id": "local"}, previous_hash=ZERO_HASH, events=[resolved])
        state = replay([batch])
        self.assertEqual(state.requests["pure"].status, "resolved")
        self.assertIsNone(state.requests["pure"].reservation_sequence)
        bad = EventBatch.create(sequence=2, batch_id="conflict", request_id="pure",
            request_sha256=canonical_sha256("different"), work_id="work-1", occurred_at="2026-09-11T00:00:01Z",
            actor={"type": "test", "id": "local"}, previous_hash=batch.batch_hash,
            events=[DomainEvent("REQUEST_RESOLVED", {**payload, "request_sha256": canonical_sha256("different")})])
        with self.assertRaisesRegex(IntegrityError, "REQUEST_CONFLICT"):
            replay([batch, bad])

    def test_reducer_derives_blockers_and_review_rounds_from_events(self):
        from unified_workflow.reducer import reduce_event
        state = task(status="waiting_review")
        state = apply(state, decide(state, command("RECORD_REVIEW", "task-001",
            assertion=review(state, verdict="NEEDS_FIXES")), workspace()))
        self.assertEqual(dict(state.review_rounds_by_task), {"task-001": 1})
        state = reduce_event(state, DomainEvent("SCOPE_VIOLATION", {"task_id": "task-001"}))
        self.assertEqual([dict(item) for item in state.blockers],
                         [{"task_id": "task-001", "reason_codes": ("SCOPE_VIOLATION",)}])
        state = reduce_event(state, DomainEvent("TASK_UNBLOCKED", {"task_id": "task-001",
            "provenance": {"actor": "human", "resolution": "reverted"}}))
        self.assertEqual(state.blockers, ())


class CLIWholeWorkspaceRegressions(CLIProject):
    def accept(self, identifier="A"):
        self.mutate("verify", "--task-id", identifier, "--command-id", "unit")
        self.mutate("review", "record", "--task-id", identifier,
                    "--assertion-file", self.document(self.review(identifier)))
        self.mutate("task", "accept", "--task-id", identifier)

    def add_narrow(self, identifier, filename, dependencies=(), required=True):
        raw = valid_task()
        raw.update(task_id=identifier, dependencies=list(dependencies), required=required,
                   write_scope={"allowed_paths": [filename], "forbidden_paths": []},
                   verification_inputs=[filename])
        raw["verification_commands"][0]["argv"] = [sys.executable, "-c", "pass"]
        self.mutate("task", "add", "--task-file", self.document(raw))

    def test_cli_create_modify_delete_outside_inputs_is_scope_violation(self):
        self.initialize()
        for action in ("create", "modify", "delete"):
            identifier = "task-" + action
            filename = action + ".txt"
            outside = self.root / filename
            if action != "create":
                outside.write_text("before")
            self.add(identifier)
            self.start(identifier)
            if action == "delete":
                outside.unlink()
            else:
                outside.write_text("outside scope")
            output = self.mutate("verify", "--task-id", identifier, "--command-id", "unit", code=3)
            self.assertEqual(output["reason_code"], "SCOPE_VIOLATION")
            _, state = self.store()
            self.assertEqual(state.tasks[identifier].history[-1].event_type, "SCOPE_VIOLATION")
            self.assertIn(filename, state.tasks[identifier].verifications[-1]["evidence"]["scope_diff"])

    def test_symlink_input_is_verified_and_alias_write_scope_is_enforced(self):
        (self.root / "alias.txt").symlink_to("input.txt")
        self.initialize()
        self.add_narrow("A", "alias.txt")
        self.start()
        (self.root / "input.txt").write_text("pass changed through alias")
        output = self.mutate("verify", "--task-id", "A", "--command-id", "unit", code=3)
        self.assertEqual(output["reason_code"], "SCOPE_VIOLATION")
        evidence_record = self.store()[1].tasks["A"].verifications[-1]["evidence"]
        self.assertIn("input.txt", evidence_record["scope_diff"])
        self.assertIn("alias.txt", evidence_record["scope_diff"])

    def test_distinct_task_inputs_deliver_and_later_workspace_drift_requires_new_delivery(self):
        for filename in ("alpha.txt", "beta.txt", "gamma.txt"):
            (self.root / filename).write_text(filename)
        self.initialize()
        self.add_narrow("A", "alpha.txt")
        self.add_narrow("B", "beta.txt", ["A"])
        self.add_narrow("optional", "gamma.txt", required=False)
        self.start("A")
        self.accept("A")
        self.start("B")
        (self.root / "beta.txt").write_text("B legal change")
        self.accept("B")
        state = self.store()[1]
        self.assertTrue(state.tasks["A"].currently_satisfied)
        assertion = dict(delivery_target="working_tree", acceptance_set_sha256=state.acceptance_set_sha256,
                         workspace_revision=self.observation("A").to_dict(),
                         provenance={"provider": "human", "reference": str(self.root)})
        self.mutate("delivery", "record", "--delivery-file", self.document(assertion))
        (self.root / "gamma.txt").write_text("non-required input changed")
        output = self.mutate("run", "complete", code=3)
        self.assertEqual(output["reason_code"], "EVIDENCE_STALE")
        self.assertEqual(state.acceptance_set_sha256, self.store()[1].acceptance_set_sha256)
        assertion["workspace_revision"] = self.observation("A").to_dict()
        self.mutate("delivery", "record", "--delivery-file", self.document(assertion))
        self.mutate("run", "complete")
        self.assertEqual(self.call("status"), self.call("replay"))

    def test_edit_to_accepted_input_reopens_task_and_dependent(self):
        for filename in ("alpha.txt", "beta.txt"):
            (self.root / filename).write_text(filename)
        self.initialize()
        self.add_narrow("A", "alpha.txt")
        self.add_narrow("B", "beta.txt", ["A"])
        self.start("A")
        self.accept("A")
        self.start("B")
        self.accept("B")
        (self.root / "alpha.txt").write_text("changed accepted input")
        output = self.mutate("run", "complete", code=3)
        self.assertEqual(output["reason_code"], "EVIDENCE_STALE")
        reopened = self.store()[1]
        self.assertEqual({t.status for t in reopened.tasks.values()}, {"stale"})
        self.assertEqual(reopened.tasks["B"].task_revision, 2)
        self.assertIsNone(reopened.tasks["B"].scope_origin)
        for identifier in ("A", "B"):
            self.start(identifier)
            self.accept(identifier)
        current = self.store()[1]
        self.assertTrue(all(task.currently_satisfied for task in current.tasks.values()))
        self.assertEqual(current.tasks["B"].task_revision, 2)

    def test_init_requires_explicit_goal_and_exposes_audit_fields(self):
        route = self.document(valid_route())
        self.call("init", "--route-file", route, request="missing-goal", code=2)
        self.mutate("init", "--goal", "Ship the kernel", "--route-file", route)
        state = self.call("status")["state"]
        self.assertEqual(state["goal"], "Ship the kernel")
        self.assertEqual(state["route_contract_sha256"], canonical_sha256(valid_route()))
        self.assertEqual(state["latest_sequence"], 1)
        self.assertEqual(state["review_rounds_by_task"], {})

    def test_git_ignore_preserves_existing_excludes_and_keeps_runtime_out_of_status(self):
        excludes = self.root / ".git/info/exclude"
        original = b"# project local ignores\nlocal-secret\n"
        excludes.write_bytes(original)
        self.initialize()
        self.add()
        self.start()
        self.mutate("verify", "--task-id", "A", "--command-id", "unit")
        self.assertTrue(excludes.read_bytes().startswith(original))
        for path in self.store()[0].run_dir.rglob("*"):
            if path.is_file():
                result = subprocess.run(["git", "-C", str(self.root), "check-ignore", "-q", str(path)])
                self.assertEqual(result.returncode, 0, str(path))
        status = subprocess.run(["git", "-C", str(self.root), "status", "--porcelain"],
                                capture_output=True, text=True, check=True)
        self.assertEqual(status.stdout, "")
        self.assertFalse((self.root / ".gitignore").exists())

    def test_higher_precedence_ignore_negation_gets_minimal_idempotent_fallback(self):
        ignore = self.root / ".gitignore"
        original = b"# keep original content\n!/.unified-dev-flow/\n!/.unified-dev-flow/**"
        ignore.write_bytes(original)
        self.initialize()
        result = subprocess.run(["git", "-C", str(self.root), "check-ignore", "-q",
                                 ".unified-dev-flow/runs/work-1/events.jsonl"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(ignore.read_bytes(), original + b"\n/.unified-dev-flow/\n")
        before = ignore.read_bytes()
        result = RunStore(self.root, "work-2").execute(replace(command("INIT_RUN", route=valid_route()),
                                                             work_id="work-2"))
        self.assertIsInstance(result.outcome, Allowed)
        self.assertEqual(ignore.read_bytes(), before)
        status = subprocess.run(["git", "-C", str(self.root), "status", "--porcelain"],
                                capture_output=True, text=True, check=True)
        self.assertEqual(status.stdout, "?? .gitignore\n")

    def test_linked_worktree_uses_common_git_exclude(self):
        linked = Path(self.temp.name) / "linked"
        subprocess.run(["git", "-C", str(self.root), "worktree", "add", "-q", "--detach", str(linked)], check=True)
        self.root = linked
        self.initialize()
        result = subprocess.run(["git", "-C", str(self.root), "check-ignore", "-q",
                                 ".unified-dev-flow/runs/work-1/events.jsonl"])
        self.assertEqual(result.returncode, 0)
        self.assertTrue((linked / ".git").is_file())

    def test_invalid_git_pointers_leave_external_targets_untouched(self):
        for pointer_kind in ("gitdir", "commondir"):
            for contents in ("missing", "empty", "existing"):
                with self.subTest(pointer_kind=pointer_kind, contents=contents), TemporaryDirectory() as temporary:
                    project = Path(temporary) / "project"
                    target = Path(temporary) / "not-git"
                    project.mkdir()
                    if contents != "missing":
                        target.mkdir()
                    if contents == "existing":
                        (target / "info").mkdir()
                        (target / "info/exclude").write_bytes(b"# unrelated local configuration\nkeep-me")
                    if pointer_kind == "gitdir":
                        (project / ".git").write_text("gitdir: ../not-git\n")
                    else:
                        subprocess.run(["git", "init", "-q", str(project)], check=True)
                        (project / ".git/commondir").write_text("../../not-git\n")
                    before = {path.relative_to(target).as_posix(): path.read_bytes() if path.is_file() else None
                              for path in target.rglob("*")}
                    existed = target.exists()
                    with self.assertRaisesRegex(ValidationError, "INVALID_GIT_DIRECTORY"):
                        RunStore(project, "work-1").execute(command("INIT_RUN", route=valid_route()))
                    after = {path.relative_to(target).as_posix(): path.read_bytes() if path.is_file() else None
                             for path in target.rglob("*")}
                    self.assertEqual(after, before)
                    self.assertEqual(target.exists(), existed)
                    self.assertFalse((project / ".gitignore").exists())

    def test_ignore_preflight_rejects_invalid_git_directory_output_before_writes(self):
        excludes = self.root / ".git/info/exclude"
        before = excludes.read_bytes()
        outputs = ("", "relative/git\n", str(self.root / ".git") + "\nextra\n",
                   str(Path(self.temp.name) / "unrelated") + "\n")
        for index, output in enumerate(outputs):
            with self.subTest(output=output):
                identifier = "invalid-" + str(index)
                with patch("unified_workflow.store.subprocess.run",
                           return_value=subprocess.CompletedProcess(["git"], 0, stdout=output)):
                    with self.assertRaisesRegex(ValidationError, "INVALID_GIT_DIRECTORY"):
                        RunStore(self.root, identifier).execute(replace(command("INIT_RUN", route=valid_route()),
                                                                        work_id=identifier))
                self.assertEqual(excludes.read_bytes(), before)

    def test_init_without_root_dotgit_keeps_plain_directory_ignore_fallback(self):
        for bare in (False, True):
            with self.subTest(bare=bare), TemporaryDirectory() as temporary:
                project = Path(temporary)
                if bare:
                    subprocess.run(["git", "init", "--bare", "-q", str(project)], check=True)
                original = b"# keep local rules"
                (project / ".gitignore").write_bytes(original)
                with patch("unified_workflow.store.subprocess.run",
                           side_effect=AssertionError("No root .git metadata to preflight")):
                    result = RunStore(project, "work-1").execute(command("INIT_RUN", route=valid_route()))
                self.assertIsInstance(result.outcome, Allowed)
                self.assertEqual((project / ".gitignore").read_bytes(), original + b"\n/.unified-dev-flow/\n")

    def test_ignore_preflight_timeout_leaves_configuration_untouched(self):
        excludes = self.root / ".git/info/exclude"
        before = excludes.read_bytes()
        with patch("unified_workflow.store.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("git rev-parse", 10)):
            with self.assertRaisesRegex(ValidationError, "RUNTIME_IGNORE_FAILED"):
                RunStore(self.root, "work-1").execute(command("INIT_RUN", route=valid_route()))
        self.assertEqual(excludes.read_bytes(), before)

    def test_ignore_validation_timeout_has_a_typed_failure(self):
        preflight = subprocess.CompletedProcess(["git"], 0, stdout=str(self.root.resolve() / ".git") + "\n")
        with patch("unified_workflow.store.subprocess.run",
                   side_effect=[preflight, subprocess.TimeoutExpired("git check-ignore", 10)]):
            with self.assertRaisesRegex(ValidationError, "RUNTIME_IGNORE_FAILED"):
                RunStore(self.root, "work-1").execute(command("INIT_RUN", route=valid_route()))

    def test_patch_route_leaves_git_ignore_files_untouched(self):
        excludes = self.root / ".git/info/exclude"
        before = excludes.read_bytes()
        route = valid_route()
        route["delivery_target"] = "patch"
        self.mutate("init", "--goal", "Read-only proposal", "--route-file", self.document(route), code=3)
        self.assertEqual(excludes.read_bytes(), before)
        self.assertFalse((self.root / ".gitignore").exists())
        self.assertFalse((self.root / ".unified-dev-flow").exists())


if __name__ == "__main__":
    unittest.main()
