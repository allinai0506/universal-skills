#!/usr/bin/env python3
"""Behavioral transition and freshness contracts for the pure Gate."""
from dataclasses import replace
import unittest

from test_unified_workflow_model import valid_route, valid_task, valid_review
from unified_workflow.commands import Allowed, Command, Denied
from unified_workflow.commands import Decision
from unified_workflow.events import DomainEvent
from unified_workflow.model import WorkspaceRevision, canonical_sha256
from unified_workflow.reducer import initial_state, reduce_event
from unified_workflow.gate_kernel import decide, delivery_at_or_below_ceiling


OLD = "sha256:" + "a" * 64
NEW = "sha256:" + "b" * 64


def workspace(fingerprint=OLD, paths=()):
    return WorkspaceRevision.from_dict(dict(schema_version=1, provider="mock",
        revision_id=fingerprint[7:], verification_input_fingerprint=fingerprint,
        changed_paths=list(paths), observed_at="2026-09-11T00:00:00Z"))


def command(kind, task_id=None, **payload):
    return Command.from_dict(dict(schema_version=1, request_id="request-1", command_type=kind,
        work_id="work-1", task_id=task_id, actor={"type": "test", "id": "local"},
        expected_sequence=0, payload=payload))


def apply(state, decision):
    for event in decision.events:
        state = reduce_event(state, event)
    return state


def advance(state, kind, task_id=None, facts=None, **payload):
    result = decide(state, command(kind, task_id, **payload), facts)
    assert isinstance(result.outcome, Allowed), result.outcome
    return apply(state, result)


def run(route=None):
    return advance(initial_state(), "INIT_RUN", route=route or valid_route())


def task(state=None, identifier="task-001", status="draft", **changes):
    state = run() if state is None else state
    raw = valid_task()
    raw.update(task_id=identifier, **changes)
    state = advance(state, "ADD_TASK", identifier, task=raw)
    if status != "draft":
        state = advance(state, "READY_TASK", identifier)
    if status in ("running", "waiting_review", "accepted"):
        state = advance(state, "START_TASK", identifier, facts=workspace())
    if status in ("waiting_review", "accepted"):
        state = advance(state, "RECORD_VERIFICATION", identifier, facts=workspace(),
                        evidence=evidence(state, identifier))
        state = advance(state, "WAIT_FOR_REVIEW", identifier, facts=workspace())
    if status == "accepted":
        state = advance(state, "RECORD_REVIEW", identifier, facts=workspace(),
                        assertion=review(state, identifier))
        state = advance(state, "ACCEPT_TASK", identifier, facts=workspace())
    return state


def evidence(state, identifier="task-001", **changes):
    current = state.tasks[identifier]
    verification = current.contract.verification_commands[0]
    revision = workspace().to_dict()
    raw = dict(schema_version=1, task_id=identifier, task_revision=current.task_revision,
        task_contract_sha256=canonical_sha256(current.contract.to_dict()),
        command_id=verification.command_id, command_sha256=canonical_sha256(verification.to_dict()),
        provider="mock", provider_version="1", pre_command_revision=revision,
        post_command_revision=revision, commit_revision=revision,
        started_at="2026-09-11T00:00:00Z", ended_at="2026-09-11T00:00:01Z",
        exit_code=0, timed_out=False, output_truncated=False, stdout_bytes=0,
        stdout_sha256=canonical_sha256(""), stdout_blob_ref=None, stderr_bytes=0,
        stderr_sha256=canonical_sha256(""), stderr_blob_ref=None, scope_diff=[],
        verification_input_fingerprint=OLD)
    raw.update(changes)
    raw["evidence_sha256"] = canonical_sha256(raw)
    return raw


def review(state, identifier="task-001", **changes):
    current = state.tasks[identifier]
    latest = {item["evidence"]["command_id"]: item["evidence"]["evidence_sha256"]
              for item in current.verifications
              if item["evidence"]["task_revision"] == current.task_revision}
    raw = valid_review()
    raw.update(task_id=identifier, task_revision=current.task_revision,
        task_contract_sha256=canonical_sha256(current.contract.to_dict()),
        source_fingerprint=OLD,
        test_fingerprint=canonical_sha256([item.to_dict() for item in current.contract.verification_commands]),
        evidence_fingerprint=canonical_sha256(list(latest.values())))
    raw.update(changes)
    raw.pop("assertion_sha256")
    raw["assertion_sha256"] = canonical_sha256(raw)
    return raw


def delivery(state, target="working_tree", digest=None):
    return command("RECORD_DELIVERY", delivery_target=target,
        acceptance_set_sha256=digest or state.acceptance_set_sha256,
        workspace_revision=workspace().to_dict(), provenance={"provider": "mock", "reference": "result-1"})


class GateTests(unittest.TestCase):
    def denied(self, result, code, names=()):
        self.assertIsInstance(result.outcome, Denied)
        self.assertEqual(result.outcome.reason_code, code)
        self.assertTrue(result.outcome.required_actions)
        self.assertEqual([item.event_type for item in result.events], list(names))

    def test_patch_init_denied(self):
        raw = valid_route()
        raw["delivery_target"] = "patch"
        self.denied(decide(initial_state(), command("INIT_RUN", route=raw)), "RUNTIME_NOT_AUTHORIZED")

    def test_invalid_contract_and_transition(self):
        state = run()
        self.denied(decide(state, command("ADD_TASK", "bad", task={})), "INVALID_CONTRACT")
        self.denied(decide(state, command("START_TASK", "missing")), "INVALID_TRANSITION")
        self.denied(decide(task(), command("ACCEPT_TASK", "task-001")), "INVALID_TRANSITION")

    def test_dependencies_checked_at_ready_and_start(self):
        state = task(identifier="upstream")
        state = task(state, dependencies=["upstream"])
        self.denied(decide(state, command("READY_TASK", "task-001")), "DEPENDENCY_NOT_SATISFIED")
        state = reduce_event(state, DomainEvent("TASK_READIED", {"task_id": "task-001"}))
        self.denied(decide(state, command("START_TASK", "task-001"), workspace()), "DEPENDENCY_NOT_SATISFIED")

    def test_one_running_writable_task(self):
        state = task(identifier="upstream", status="running")
        state = task(state, status="ready")
        self.denied(decide(state, command("START_TASK", "task-001"), workspace()), "INVALID_TRANSITION")

    def test_scope_origin_survives_needs_fixes_retry(self):
        state = task(status="waiting_review")
        origin = state.tasks["task-001"].scope_origin
        state = advance(state, "RECORD_REVIEW", "task-001", facts=workspace(),
                        assertion=review(state, verdict="NEEDS_FIXES"))
        self.assertEqual(state.tasks["task-001"].review_round, 1)
        self.assertEqual(state.tasks["task-001"].task_revision, 1)
        state = advance(state, "START_TASK", "task-001", facts=workspace(NEW))
        self.assertEqual(state.tasks["task-001"].scope_origin, origin)
        self.denied(decide(state, command("WAIT_FOR_REVIEW", "task-001"), workspace()), "EVIDENCE_MISSING")

    def test_scope_violation_persists_across_invalidation(self):
        state = task(status="running")
        result = decide(state, command("REPORT_TASK", "task-001", report={"summary": "done"},
                        workspace_revision=workspace(paths=["secret.txt"]).to_dict()),
                        workspace(paths=["secret.txt"]))
        self.denied(result, "SCOPE_VIOLATION", ["SCOPE_VIOLATION"])
        state = apply(state, result)
        state = reduce_event(state, DomainEvent("TASK_INVALIDATED", {"task_id": "task-001", "new_task_revision": 2}))
        self.denied(decide(state, command("READY_TASK", "task-001")), "SCOPE_VIOLATION")
        self.denied(decide(state, command("RESOLVE_BLOCKER", "task-001")), "PROVENANCE_INSUFFICIENT")
        state = advance(state, "RESOLVE_BLOCKER", "task-001", provenance={"actor": "human", "resolution": "reverted"})
        state = advance(state, "START_TASK", "task-001", facts=workspace(NEW))
        self.assertEqual(state.tasks["task-001"].scope_origin["verification_input_fingerprint"], OLD)

    def test_report_requires_matching_commit_observation(self):
        state = task(status="running")
        self.denied(decide(state, command("REPORT_TASK", "task-001", report={"summary": "ok"},
                    workspace_revision=workspace().to_dict()), workspace(NEW)), "EVIDENCE_STALE")
        state = advance(state, "REPORT_TASK", "task-001", facts=workspace(),
                    report={"summary": "ok"}, workspace_revision=workspace().to_dict())
        self.assertEqual(state.tasks["task-001"].reports[-1]["report"]["summary"], "ok")

    def test_verification_failure_is_recorded_and_returns_ready(self):
        for changes in ({"exit_code": 1}, {"timed_out": True}, {"output_truncated": True}):
            state = task(status="running")
            result = decide(state, command("RECORD_VERIFICATION", "task-001", evidence=evidence(state, **changes)), workspace())
            self.denied(result, "EVIDENCE_MISSING", ["VERIFICATION_RECORDED"])
            self.assertFalse(result.events[0].payload["success"])
            self.assertEqual(apply(state, result).tasks["task-001"].status, "ready")

    def test_verification_stale_and_scope_facts_are_recorded(self):
        state = task(status="running")
        result = decide(state, command("RECORD_VERIFICATION", "task-001",
            evidence=evidence(state, post_command_revision=workspace(NEW).to_dict())), workspace())
        self.denied(result, "EVIDENCE_STALE", ["VERIFICATION_RECORDED"])
        result = decide(state, command("RECORD_VERIFICATION", "task-001",
            evidence=evidence(state, scope_diff=["secret.txt"])), workspace())
        self.denied(result, "SCOPE_VIOLATION", ["VERIFICATION_RECORDED", "SCOPE_VIOLATION"])

    def test_verification_requires_matching_command_contract_and_digest(self):
        state = task(status="running")
        for changes in ({"command_sha256": NEW}, {"task_revision": 2}, {"task_contract_sha256": NEW}):
            result = decide(state, command("RECORD_VERIFICATION", "task-001", evidence=evidence(state, **changes)), workspace())
            self.assertEqual(result.outcome.reason_code, "EVIDENCE_STALE")
        raw = evidence(state)
        raw["exit_code"] = 1
        self.denied(decide(state, command("RECORD_VERIFICATION", "task-001", evidence=raw), workspace()), "INVALID_CONTRACT")

    def test_wait_requires_evidence_and_claim_union(self):
        state = task(status="running")
        self.denied(decide(state, command("WAIT_FOR_REVIEW", "task-001"), workspace()), "EVIDENCE_MISSING")
        raw = valid_task()["verification_commands"]
        raw[0]["claims"] = ["deterministic"]
        state = task(status="running", verification_commands=raw)
        state = advance(state, "RECORD_VERIFICATION", "task-001", facts=workspace(), evidence=evidence(state))
        self.denied(decide(state, command("WAIT_FOR_REVIEW", "task-001"), workspace()), "EVIDENCE_MISSING")

    def test_review_provenance_and_freshness(self):
        state = task(status="waiting_review")
        self.denied(decide(state, command("ACCEPT_TASK", "task-001"), workspace()), "VERDICT_MISSING")
        self.denied(decide(state, command("RECORD_REVIEW", "task-001", assertion=review(state, provenance="mock")), workspace()), "PROVENANCE_INSUFFICIENT")
        for field in ("source_fingerprint", "test_fingerprint", "evidence_fingerprint", "task_contract_sha256"):
            self.denied(decide(state, command("RECORD_REVIEW", "task-001", assertion=review(state, **{field: NEW})), workspace()), "VERDICT_STALE")

    def test_third_needs_fixes_is_one_escalation_batch(self):
        for limit, round_number, escalates in ((3, 2, True), (3, 1, False), (2, 1, True)):
            raw = valid_route()
            raw["review_limit"] = limit
            state = task(run(raw), status="waiting_review")
            state = replace(state, tasks={"task-001": replace(state.tasks["task-001"], review_round=round_number)})
            result = decide(state, command("RECORD_REVIEW", "task-001", assertion=review(state, verdict="NEEDS_FIXES")), workspace())
            expected = (["REVIEW_RECORDED", "TASK_INVALIDATED", "TASK_BLOCKED", "RUN_BLOCKED", "ESCALATE_TO_HUMAN"]
                        if escalates else ["REVIEW_RECORDED", "TASK_NEEDS_FIXES"])
            self.assertEqual([item.event_type for item in result.events], expected)
            if escalates:
                self.assertEqual(result.outcome.reason_code, "REVIEW_LIMIT_REACHED")
                self.assertEqual(apply(state, result).status, "blocked")

    def test_denied_completion_persists_input_invalidation_and_cascades(self):
        state = task(identifier="upstream", status="accepted")
        state = task(state, status="accepted", dependencies=["upstream"])
        result = decide(state, command("COMPLETE_RUN"), {"task_workspaces": {"upstream": workspace(NEW)}})
        self.denied(result, "EVIDENCE_STALE", ["TASK_INVALIDATED"])
        changed = apply(state, result)
        self.assertEqual(changed.tasks["upstream"].status, "stale")
        self.assertEqual(changed.tasks["task-001"].status, "stale")
        self.assertTrue(state.tasks["task-001"].currently_satisfied)

    def test_delivery_must_bind_current_acceptance_set(self):
        state = task(status="accepted")
        self.denied(decide(state, delivery(state, digest=NEW), workspace()), "EVIDENCE_STALE")
        self.denied(decide(state, delivery(state, target="pr"), workspace()), "DELIVERY_NOT_AUTHORIZED")

    def test_every_delivery_ceiling_pair(self):
        order = ("patch", "working_tree", "commit", "pr", "merge", "deploy")
        for i, target in enumerate(order):
            for j, ceiling in enumerate(order):
                self.assertEqual(delivery_at_or_below_ceiling(target, ceiling), i <= j)

    def test_completion_required_optional_cancelled_and_delivery(self):
        state = task(status="accepted")
        self.denied(decide(state, command("COMPLETE_RUN"), workspace()), "EVIDENCE_MISSING")
        state = apply(state, decide(state, delivery(state), workspace()))
        state = task(state, identifier="optional", required=False)
        state = advance(state, "CANCEL_TASK", "optional")
        completed = advance(state, "COMPLETE_RUN", facts=workspace())
        self.assertEqual(completed.status, "completed")
        state = advance(state, "CANCEL_TASK", "task-001")
        self.denied(decide(state, command("COMPLETE_RUN"), workspace()), "DEPENDENCY_NOT_SATISFIED")

    def test_cancel_run_terminal_and_no_lifecycle_events(self):
        state = task(status="running")
        result = decide(state, command("CANCEL_RUN"))
        self.assertEqual([e.event_type for e in result.events], ["TASK_CANCELLED", "RUN_CANCELLED"])
        self.denied(decide(apply(state, result), command("READY_TASK", "task-001")), "INVALID_TRANSITION")

    def test_completion_cannot_reuse_acceptance_without_current_observation(self):
        state = task(status="accepted")
        state = apply(state, decide(state, delivery(state), workspace()))
        self.denied(decide(state, command("COMPLETE_RUN")), "EVIDENCE_MISSING")

    def test_delivery_requires_every_required_task_accepted(self):
        state = task()
        self.denied(decide(state, delivery(state), workspace()), "DEPENDENCY_NOT_SATISFIED")

    def test_decision_domain_events_serialize_for_store(self):
        result = decide(initial_state(), command("INIT_RUN", route=valid_route()))
        serialized = result.to_dict()
        self.assertEqual(serialized["events"][0]["event_type"], "RUN_CREATED")
        self.assertEqual(Decision.from_dict(serialized).to_dict(), serialized)

    def test_unknown_command_payload_fields_rejected(self):
        self.denied(decide(run(), command("ADD_TASK", "task-001", task=valid_task(), bypass=True)), "INVALID_CONTRACT")

    def test_third_round_is_retained_in_replayed_state(self):
        state = task(status="waiting_review")
        state = replace(state, tasks={"task-001": replace(state.tasks["task-001"], review_round=2)})
        result = decide(state, command("RECORD_REVIEW", "task-001", assertion=review(state, verdict="NEEDS_FIXES")), workspace())
        self.assertEqual(apply(state, result).tasks["task-001"].review_round, 3)

    def test_scope_is_checked_before_wait_even_without_input_change(self):
        state = task(status="running")
        state = advance(state, "RECORD_VERIFICATION", "task-001", facts=workspace(), evidence=evidence(state))
        self.denied(decide(state, command("WAIT_FOR_REVIEW", "task-001"), workspace(paths=["secret.txt"])),
                    "SCOPE_VIOLATION", ["SCOPE_VIOLATION"])

    def test_reobserving_same_revision_at_later_time_allows_report_and_delivery(self):
        state = task(status="running")
        later = replace(workspace(), observed_at="2026-09-11T01:00:00Z")
        state = advance(state, "REPORT_TASK", "task-001", facts=later,
                        workspace_revision=workspace().to_dict(), report={"summary": "done"})
        state = task(status="accepted")
        self.assertIsInstance(decide(state, delivery(state), later).outcome, Allowed)

    def test_old_delivery_does_not_complete_reaccepted_task(self):
        state = task(status="accepted")
        state = apply(state, decide(state, delivery(state), workspace()))
        state = reduce_event(state, DomainEvent("TASK_INVALIDATED", {"task_id": "task-001", "new_task_revision": 2}))
        state = advance(state, "READY_TASK", "task-001")
        state = advance(state, "START_TASK", "task-001", facts=workspace())
        state = advance(state, "RECORD_VERIFICATION", "task-001", facts=workspace(), evidence=evidence(state))
        state = advance(state, "WAIT_FOR_REVIEW", "task-001", facts=workspace())
        state = advance(state, "RECORD_REVIEW", "task-001", facts=workspace(), assertion=review(state))
        state = advance(state, "ACCEPT_TASK", "task-001", facts=workspace())
        self.denied(decide(state, command("COMPLETE_RUN"), workspace()), "EVIDENCE_MISSING")

    def test_claims_union_across_distinct_commands(self):
        commands = valid_task()["verification_commands"]
        commands[0]["claims"] = ["deterministic"]
        commands.append({**commands[0], "command_id": "adversarial", "claims": ["adversarial"]})
        state = task(status="running", verification_commands=commands)
        state = advance(state, "RECORD_VERIFICATION", "task-001", facts=workspace(), evidence=evidence(state))
        self.denied(decide(state, command("WAIT_FOR_REVIEW", "task-001"), workspace()), "EVIDENCE_MISSING")
        state = advance(state, "RECORD_VERIFICATION", "task-001", facts=workspace(),
            evidence=evidence(state, command_id="adversarial", command_sha256=canonical_sha256(commands[1])))
        state = advance(state, "WAIT_FOR_REVIEW", "task-001", facts=workspace())
        self.assertEqual(state.tasks["task-001"].status, "waiting_review")

    def test_complete_three_round_retry_lifecycle(self):
        state = task(status="waiting_review")
        for round_number in range(3):
            result = decide(state, command("RECORD_REVIEW", "task-001", assertion=review(state, verdict="NEEDS_FIXES")), workspace())
            state = apply(state, result)
            self.assertEqual(state.tasks["task-001"].review_round, round_number + 1)
            if round_number < 2:
                state = advance(state, "START_TASK", "task-001", facts=workspace())
                state = advance(state, "RECORD_VERIFICATION", "task-001", facts=workspace(), evidence=evidence(state))
                state = advance(state, "WAIT_FOR_REVIEW", "task-001", facts=workspace())
        self.assertEqual(state.status, "blocked")

    def test_component_globs_do_not_allow_deeper_writes(self):
        state = task(status="running", write_scope={"allowed_paths": ["src/*"], "forbidden_paths": []})
        self.denied(decide(state, command("WAIT_FOR_REVIEW", "task-001"), workspace(paths=["src/nested/file.py"])),
                    "SCOPE_VIOLATION", ["SCOPE_VIOLATION"])

    def test_missing_dependency_observation_prevents_completion(self):
        state = task(identifier="upstream", status="accepted", required=False)
        state = task(state, status="accepted", dependencies=["upstream"])
        state = apply(state, decide(state, delivery(state), workspace()))
        self.denied(decide(state, command("COMPLETE_RUN"), {"task_workspaces": {"task-001": workspace()}}), "EVIDENCE_MISSING")

    def test_input_change_after_verification_persists_invalidation_before_wait(self):
        state = task(status="running")
        state = advance(state, "RECORD_VERIFICATION", "task-001", facts=workspace(), evidence=evidence(state))
        self.denied(decide(state, command("WAIT_FOR_REVIEW", "task-001"), workspace(NEW)),
                    "EVIDENCE_STALE", ["TASK_INVALIDATED"])

    def test_accepted_scope_violation_blocks_delivery_and_completion(self):
        state = task(status="accepted")
        state = apply(state, decide(state, delivery(state), workspace()))
        for operation in (delivery(state), command("COMPLETE_RUN")):
            with self.subTest(command=operation.command_type):
                result = decide(state, operation, workspace(paths=["secret.txt"]))
                self.denied(result, "SCOPE_VIOLATION", ["SCOPE_VIOLATION"])
                self.assertEqual(apply(state, result).tasks["task-001"].status, "blocked")

    def test_missing_observation_records_failure_without_invalidation(self):
        state = task(status="running")
        origin = state.tasks["task-001"].scope_origin
        result = decide(state, command("RECORD_VERIFICATION", "task-001", evidence=evidence(state)))
        self.denied(result, "EVIDENCE_MISSING", ["VERIFICATION_RECORDED"])
        changed = apply(state, result)
        self.assertEqual(changed.tasks["task-001"].task_revision, 1)
        self.assertEqual(changed.tasks["task-001"].scope_origin, origin)

    def test_malformed_evidence_binding_does_not_invalidate_even_with_new_observation(self):
        state = task(status="running")
        for changes in ({"task_id": "wrong"}, {"task_revision": 2}, {"task_contract_sha256": NEW}, {"command_sha256": NEW}):
            with self.subTest(changes=changes):
                result = decide(state, command("RECORD_VERIFICATION", "task-001", evidence=evidence(state, **changes)), workspace(NEW))
                self.denied(result, "EVIDENCE_STALE", ["VERIFICATION_RECORDED"])
                self.assertEqual(apply(state, result).tasks["task-001"].task_revision, 1)

    def test_current_observation_proving_drift_does_invalidate(self):
        state = task(status="running")
        result = decide(state, command("RECORD_VERIFICATION", "task-001", evidence=evidence(state)), workspace(NEW))
        self.denied(result, "EVIDENCE_STALE", ["VERIFICATION_RECORDED", "TASK_INVALIDATED"])
        self.assertEqual(apply(state, result).tasks["task-001"].task_revision, 2)

    def test_inconsistent_top_level_fingerprint_is_not_observed_input_drift(self):
        state = task(status="running")
        observed = workspace(NEW)
        raw = evidence(state, pre_command_revision=observed.to_dict(),
                       post_command_revision=observed.to_dict(), commit_revision=observed.to_dict(),
                       verification_input_fingerprint=OLD)
        result = decide(state, command("RECORD_VERIFICATION", "task-001", evidence=raw), observed)
        self.denied(result, "EVIDENCE_STALE", ["VERIFICATION_RECORDED"])
        self.assertEqual(apply(state, result).tasks["task-001"].task_revision, 1)

    def test_inconsistent_recorded_revisions_cannot_establish_old_input_binding(self):
        state = task(status="running")
        for field in ("pre_command_revision", "post_command_revision", "commit_revision"):
            with self.subTest(field=field):
                raw = evidence(state, **{field: workspace(NEW).to_dict()})
                result = decide(state, command("RECORD_VERIFICATION", "task-001", evidence=raw), workspace(NEW))
                self.denied(result, "EVIDENCE_STALE", ["VERIFICATION_RECORDED"])

    def test_rejected_evidence_cannot_become_a_later_invalidation_baseline(self):
        state = task(status="running")
        result = decide(state, command("RECORD_VERIFICATION", "task-001", evidence=evidence(state)))
        state = apply(state, result)
        state = advance(state, "START_TASK", "task-001", facts=workspace(NEW))
        self.denied(decide(state, command("WAIT_FOR_REVIEW", "task-001"), workspace(NEW)), "EVIDENCE_MISSING")

    def test_review_limit_preserves_revision_origin_for_human_retry(self):
        state = task(status="waiting_review")
        state = replace(state, tasks={"task-001": replace(state.tasks["task-001"], review_round=2)})
        origin = state.tasks["task-001"].scope_origin
        result = decide(state, command("RECORD_REVIEW", "task-001", assertion=review(state, verdict="NEEDS_FIXES")), workspace())
        state = apply(state, result)
        self.assertEqual(state.tasks["task-001"].task_revision, 1)
        self.assertEqual(state.tasks["task-001"].scope_origin, origin)
        state = advance(state, "RESOLVE_BLOCKER", "task-001", provenance={"actor": "human", "resolution": "approved retry"})
        state = advance(state, "START_TASK", "task-001", facts=workspace(NEW))
        self.assertEqual(state.tasks["task-001"].scope_origin, origin)


if __name__ == "__main__":
    unittest.main()
