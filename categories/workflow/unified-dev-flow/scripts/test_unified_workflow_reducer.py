#!/usr/bin/env python3
"""Behavioral tests for immutable event batches and workflow replay."""
from __future__ import annotations

import unittest

from unified_workflow.events import (
    ZERO_HASH,
    DomainEvent,
    EventBatch,
    IntegrityError,
)
from unified_workflow.reducer import replay


DIGEST = "sha256:" + "a" * 64


def task_contract(task_id: str, dependencies: list[str] | None = None) -> dict:
    return {
        "schema_version": 1,
        "task_id": task_id,
        "objective": f"Complete {task_id}.",
        "required": True,
        "dependencies": dependencies or [],
        "write_scope": {"allowed_paths": ["src/**"], "forbidden_paths": []},
        "verification_inputs": ["src/**"],
        "acceptance": [f"{task_id} is accepted."],
        "verification_commands": [],
        "proof_mode": "acceptance_test",
        "required_review": "none",
    }


def event(event_type: str, payload: dict | None = None) -> DomainEvent:
    return DomainEvent.from_dict({"event_type": event_type, "payload": payload or {}})


def make_batch(sequence: int, previous_hash: str, events: list[DomainEvent]) -> EventBatch:
    return EventBatch.create(
        sequence=sequence,
        batch_id=f"batch-{sequence}",
        request_id=f"request-{sequence}",
        request_sha256=DIGEST,
        work_id="work-1",
        occurred_at="2026-09-11T00:00:00Z",
        actor={"type": "test", "id": "local"},
        previous_hash=previous_hash,
        events=events,
    )


def batches(*events: DomainEvent) -> list[EventBatch]:
    previous = ZERO_HASH
    result = []
    for sequence, item in enumerate(events, start=1):
        batch = make_batch(sequence, previous, [item])
        result.append(batch)
        previous = batch.batch_hash
    return result


def accepted_history() -> list[EventBatch]:
    return batches(
        event("RUN_CREATED", {"work_id": "work-1"}),
        event("TASK_ADDED", {"task": task_contract("a")}),
        event("TASK_READIED", {"task_id": "a"}),
        event("TASK_STARTED", {"task_id": "a", "scope_origin": "origin-1"}),
        event("TASK_WAITING_REVIEW", {"task_id": "a"}),
        event("REVIEW_RECORDED", {"task_id": "a", "verdict_fingerprint": DIGEST}),
        event("TASK_ACCEPTED", {"task_id": "a", "input_fingerprint": DIGEST,
                                "verdict_fingerprint": DIGEST}),
    )


class EventReplayTests(unittest.TestCase):
    def test_replay_rejects_broken_hash_chain(self):
        first = make_batch(1, ZERO_HASH, [event("RUN_CREATED", {"work_id": "work-1"})])
        second = make_batch(2, first.batch_hash, [event("TASK_ADDED", {"task": task_contract("a")})])
        raw = second.to_dict()
        raw["previous_hash"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(IntegrityError, "EVENT_HASH_MISMATCH"):
            replay([first, EventBatch.from_dict(raw)])

    def test_replay_rejects_schema_sequence_and_batch_hash_tampering(self):
        first = make_batch(1, ZERO_HASH, [event("RUN_CREATED", {"work_id": "work-1"})])
        with self.assertRaisesRegex(IntegrityError, "EVENT_SEQUENCE_MISMATCH"):
            replay([make_batch(2, ZERO_HASH, first.events)])
        raw = first.to_dict()
        raw["events"][0]["payload"]["work_id"] = "changed"
        with self.assertRaisesRegex(IntegrityError, "EVENT_HASH_MISMATCH"):
            replay([EventBatch.from_dict(raw)])

    def test_request_without_resolution_is_in_doubt(self):
        state = replay(batches(event("REQUEST_RESERVED", {
            "request_id": "req-1", "request_sha256": DIGEST, "command_type": "START_TASK",
            "reservation_sequence": 1,
        })))
        self.assertEqual(state.requests["req-1"].status, "in_doubt")

    def test_duplicate_resolution_is_idempotent_but_conflict_is_rejected(self):
        reserved = event("REQUEST_RESERVED", {
            "request_id": "req-1", "request_sha256": DIGEST, "command_type": "START_TASK",
            "reservation_sequence": 1,
        })
        resolved = event("REQUEST_RESOLVED", {
            "request_id": "req-1", "outcome": "success", "reason_code": None,
            "result_summary": {"ok": True}, "event_ids": ["batch-1"],
        })
        state = replay(batches(reserved, resolved, resolved))
        self.assertEqual(state.requests["req-1"].outcome, "success")
        conflicting = event("REQUEST_RESOLVED", {
            "request_id": "req-1", "outcome": "denied", "reason_code": "BLOCKED",
            "result_summary": {"ok": False}, "event_ids": ["batch-2"],
        })
        with self.assertRaisesRegex(IntegrityError, "REQUEST_RESOLUTION_CONFLICT"):
            replay(batches(reserved, resolved, conflicting))

    def test_task_transitions_and_review_rounds_preserve_scope_origin(self):
        state = replay(batches(
            event("RUN_CREATED", {"work_id": "work-1"}),
            event("TASK_ADDED", {"task": task_contract("a")}),
            event("TASK_READIED", {"task_id": "a"}),
            event("TASK_STARTED", {"task_id": "a", "scope_origin": "origin-1"}),
            event("TASK_REPORTED", {"task_id": "a", "report": {"revision": "r1"}}),
            event("VERIFICATION_RECORDED", {"task_id": "a", "success": False}),
            event("TASK_STARTED", {"task_id": "a"}),
            event("TASK_WAITING_REVIEW", {"task_id": "a"}),
            event("TASK_NEEDS_FIXES", {"task_id": "a"}),
            event("TASK_WAITING_REVIEW", {"task_id": "a"}),
            event("TASK_NEEDS_FIXES", {"task_id": "a"}),
        ))
        task = state.tasks["a"]
        self.assertEqual(task.status, "ready")
        self.assertEqual(task.review_round, 2)
        self.assertEqual(task.scope_origin, "origin-1")

        state = replay(batches(
            event("RUN_CREATED", {"work_id": "work-1"}),
            event("TASK_ADDED", {"task": task_contract("a")}),
            event("TASK_BLOCKED", {"task_id": "a"}),
            event("TASK_UNBLOCKED", {"task_id": "a"}),
            event("TASK_FAILED", {"task_id": "a"}),
            event("TASK_CANCELLED", {"task_id": "a"}),
        ))
        self.assertEqual(state.tasks["a"].status, "cancelled")

    def test_third_needs_fixes_blocks_only_that_task_and_run(self):
        state = replay(batches(
            event("RUN_CREATED", {"work_id": "work-1"}),
            event("TASK_ADDED", {"task": task_contract("a")}),
            event("TASK_NEEDS_FIXES", {"task_id": "a"}),
            event("TASK_NEEDS_FIXES", {"task_id": "a"}),
            event("TASK_NEEDS_FIXES", {"task_id": "a"}),
        ))
        self.assertEqual(state.tasks["a"].review_round, 3)
        self.assertEqual(state.tasks["a"].status, "blocked")
        self.assertEqual(state.status, "blocked")

    def test_invalidation_reopens_acceptance_and_transitive_dependents_as_stale(self):
        history = accepted_history()
        previous = history[-1].batch_hash
        history.extend([
            make_batch(8, previous, [event("TASK_ADDED", {"task": task_contract("b", ["a"])})]),
        ])
        history.append(make_batch(9, history[-1].batch_hash, [event("TASK_INVALIDATED", {
            "task_id": "a", "new_task_revision": 2,
        })]))
        state = replay(history)
        self.assertEqual(state.tasks["a"].status, "stale")
        self.assertEqual(state.tasks["a"].task_revision, 2)
        self.assertFalse(state.tasks["a"].currently_satisfied)
        self.assertEqual(state.tasks["b"].status, "stale")
        self.assertEqual(state.tasks["b"].task_revision, 1)

    def test_dependency_satisfaction_current_fingerprints_and_delivery_assertions(self):
        state = replay(accepted_history())
        task = state.tasks["a"]
        self.assertTrue(task.currently_satisfied)
        self.assertEqual(task.accepted_input_fingerprint, DIGEST)
        self.assertEqual(task.accepted_verdict_fingerprint, DIGEST)

        history = accepted_history()
        history.append(make_batch(8, history[-1].batch_hash, [event("DELIVERY_RECORDED", {
            "delivery_target": "commit", "acceptance_set_sha256": state.acceptance_set_sha256,
            "provenance": {"commit": "abc123"},
        })]))
        replayed = replay(history)
        self.assertEqual(replayed.deliveries[0]["delivery_target"], "commit")
        self.assertEqual(replayed.deliveries[0]["acceptance_set_sha256"], state.acceptance_set_sha256)

    def test_dependent_task_is_satisfied_only_while_its_dependency_is_current(self):
        state = replay(batches(
            event("RUN_CREATED", {"work_id": "work-1"}),
            event("TASK_ADDED", {"task": task_contract("a")}),
            event("TASK_READIED", {"task_id": "a"}),
            event("TASK_STARTED", {"task_id": "a", "scope_origin": "origin-a"}),
            event("TASK_WAITING_REVIEW", {"task_id": "a"}),
            event("TASK_ACCEPTED", {"task_id": "a", "input_fingerprint": DIGEST,
                                    "verdict_fingerprint": DIGEST}),
            event("TASK_ADDED", {"task": task_contract("b", ["a"])}),
            event("TASK_READIED", {"task_id": "b"}),
            event("TASK_STARTED", {"task_id": "b", "scope_origin": "origin-b"}),
            event("TASK_WAITING_REVIEW", {"task_id": "b"}),
            event("TASK_ACCEPTED", {"task_id": "b", "input_fingerprint": DIGEST,
                                    "verdict_fingerprint": DIGEST}),
        ))
        self.assertTrue(state.tasks["b"].currently_satisfied)

    def test_replay_is_deterministic_and_returns_immutable_state(self):
        history = accepted_history()
        left, right = replay(history), replay(history)
        self.assertEqual(left, right)
        with self.assertRaises(TypeError):
            left.tasks["new"] = left.tasks["a"]  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
