#!/usr/bin/env python3
"""Acceptance tests for strict Unified Workflow protocol value objects."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from unified_workflow.commands import Command, Decision, Denied
from unified_workflow.model import (
    ReviewAssertion,
    RouteContract,
    TaskContract,
    ValidationError,
    canonical_sha256,
    resolve_project_path,
)


def valid_route() -> dict:
    return {
        "schema_version": 1,
        "resume": "fresh",
        "intent": "feature",
        "complexity": "medium",
        "risks": ["state_machine"],
        "domains": [],
        "delivery_target": "working_tree",
        "spec_backend": "unified",
        "controller": None,
        "proof_mode": "acceptance_test",
        "assurance_level": "adversarial",
        "review_limit": 3,
        "obligations": {
            "verification_claims": ["deterministic", "adversarial"],
            "accepted_review_provenance": ["cross_model", "human"],
            "required_delivery": "working_tree",
        },
        "source": {
            "policy_version": "2026.09.10-2",
            "policy_sha256": "sha256:" + "a" * 64,
        },
    }


def valid_task() -> dict:
    return {
        "schema_version": 1,
        "task_id": "task-001",
        "objective": "Implement an observable acceptance condition.",
        "required": True,
        "dependencies": [],
        "write_scope": {
            "allowed_paths": ["src/**", "tests/**"],
            "forbidden_paths": [".env", ".git/**", ".unified-dev-flow/**"],
        },
        "verification_inputs": ["src/**", "tests/**", "pyproject.toml"],
        "acceptance": ["The acceptance test passes."],
        "verification_commands": [{
            "command_id": "unit",
            "argv": ["python3", "-m", "unittest"],
            "cwd": ".",
            "timeout_seconds": 60,
            "max_output_bytes": 1048576,
            "required": True,
            "claims": ["deterministic", "adversarial"],
        }],
        "proof_mode": "acceptance_test",
        "required_review": "provenance_assertion",
    }


def valid_review() -> dict:
    digest = "sha256:" + "b" * 64
    return {
        "schema_version": 1,
        "task_id": "task-001",
        "task_revision": 1,
        "reviewer": "reviewer-1",
        "provider": "provider-1",
        "provenance": "cross_model",
        "task_contract_sha256": digest,
        "source_fingerprint": digest,
        "test_fingerprint": digest,
        "evidence_fingerprint": digest,
        "verdict": "MERGE_READY",
        "findings": [],
        "reviewed_at": "2026-09-11T00:00:00Z",
        "assertion_sha256": digest,
    }


class StrictModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "project"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_route_contract_rejects_unknown_field(self):
        raw = valid_route()
        raw["surprise"] = True
        with self.assertRaisesRegex(ValidationError, "UNKNOWN_FIELD"):
            RouteContract.from_dict(raw)

    def test_patch_route_is_valid_data_but_runtime_ineligible(self):
        raw = valid_route()
        raw["delivery_target"] = "patch"
        route = RouteContract.from_dict(raw)
        self.assertEqual(route.delivery_target, "patch")

    def test_task_rejects_control_directory_write(self):
        raw = valid_task()
        raw["write_scope"]["allowed_paths"] = [".unified-dev-flow/**"]
        with self.assertRaisesRegex(ValidationError, "CONTROL_PATH"):
            TaskContract.from_dict(raw)

    def test_resolved_path_rejects_symlink_escape(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        (self.root / "link").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValidationError, "PATH_ESCAPE"):
            resolve_project_path(self.root, "link/file", "cwd")

    def test_resolved_path_rejects_symlink_into_control_directory(self):
        (self.root / ".git").mkdir()
        (self.root / "control-alias").symlink_to(self.root / ".git", target_is_directory=True)
        with self.assertRaisesRegex(ValidationError, "CONTROL_PATH"):
            resolve_project_path(self.root, "control-alias/config", "cwd")

    def test_canonical_hash_is_key_order_independent(self):
        self.assertEqual(canonical_sha256({"b": 2, "a": 1}),
                         canonical_sha256({"a": 1, "b": 2}))

    def test_schema_rejects_boolean_in_integer_field(self):
        raw = valid_route()
        raw["review_limit"] = True
        with self.assertRaisesRegex(ValidationError, "INVALID_TYPE"):
            RouteContract.from_dict(raw)

    def test_schema_rejects_unknown_enum_and_duplicate_list_value(self):
        raw = valid_route()
        raw["intent"] = "surprise"
        with self.assertRaisesRegex(ValidationError, "UNKNOWN_ENUM"):
            RouteContract.from_dict(raw)
        raw = valid_task()
        raw["dependencies"] = ["task-a", "task-a"]
        with self.assertRaisesRegex(ValidationError, "DUPLICATE_VALUE"):
            TaskContract.from_dict(raw)

    def test_task_rejects_invalid_relative_paths(self):
        raw = valid_task()
        raw["write_scope"]["allowed_paths"] = ["../escape"]
        with self.assertRaisesRegex(ValidationError, "INVALID_PATH"):
            TaskContract.from_dict(raw)

    def test_command_is_strict_and_deeply_immutable(self):
        raw = {
            "schema_version": 1,
            "request_id": "request-1",
            "command_type": "START_TASK",
            "work_id": "work-1",
            "task_id": "task-1",
            "actor": {"type": "cli", "tags": ["local"]},
            "expected_sequence": 0,
            "payload": {"nested": {"value": 1}},
        }
        command = Command.from_dict(raw)
        raw["actor"]["type"] = "changed"
        self.assertEqual(command.actor["type"], "cli")
        with self.assertRaises(TypeError):
            command.actor["type"] = "changed"  # type: ignore[index]
        raw["extra"] = 1
        with self.assertRaisesRegex(ValidationError, "UNKNOWN_FIELD"):
            Command.from_dict(raw)

    def test_denied_rejects_duplicate_required_actions(self):
        with self.assertRaisesRegex(ValidationError, "DUPLICATE_VALUE"):
            Denied.from_dict({"reason_code": "BLOCKED", "required_actions": ["read", "read"]})

    def test_decision_rejects_duplicate_events(self):
        raw = {
            "events": [{"event_type": "TASK_STARTED"}, {"event_type": "TASK_STARTED"}],
            "outcome": {"kind": "allowed", "result": {"accepted": True}},
        }
        with self.assertRaisesRegex(ValidationError, "DUPLICATE_VALUE"):
            Decision.from_dict(raw)

    def test_provenance_is_closed_and_shared_by_route_and_review(self):
        self.assertEqual(ReviewAssertion.from_dict(valid_review()).provenance, "cross_model")
        raw_route = valid_route()
        raw_route["obligations"]["accepted_review_provenance"] = ["invented"]
        with self.assertRaisesRegex(ValidationError, "UNKNOWN_ENUM"):
            RouteContract.from_dict(raw_route)
        raw_review = valid_review()
        raw_review["provenance"] = "invented"
        with self.assertRaisesRegex(ValidationError, "UNKNOWN_ENUM"):
            ReviewAssertion.from_dict(raw_review)


if __name__ == "__main__":
    unittest.main()
