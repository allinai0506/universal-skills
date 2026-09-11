"""Immutable, hash-chained workflow event envelopes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import re
from types import MappingProxyType
from typing import Any, ClassVar, Mapping

from .model import (EvidenceRecord, ReviewAssertion, RouteContract, TaskContract,
                    ValidationError, WorkspaceRevision, canonical_sha256, validate_id)


ZERO_HASH = "sha256:" + "0" * 64
_EVENT_TYPES = (
    "REQUEST_RESERVED", "REQUEST_RESOLVED", "RUN_CREATED", "RUN_BLOCKED", "RUN_RESUMED",
    "RUN_COMPLETED", "RUN_CANCELLED", "TASK_ADDED", "TASK_READIED", "TASK_STARTED",
    "TASK_REPORTED", "VERIFICATION_RECORDED", "TASK_WAITING_REVIEW", "REVIEW_RECORDED",
    "TASK_NEEDS_FIXES", "TASK_ACCEPTED", "TASK_INVALIDATED", "TASK_BLOCKED",
    "TASK_UNBLOCKED", "TASK_FAILED", "TASK_CANCELLED", "SCOPE_VIOLATION",
    "ESCALATE_TO_HUMAN", "DELIVERY_RECORDED",
)
_HASH_PREFIX = "sha256:"
_UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_COMMAND_TYPES = (
    "INIT_RUN", "ADD_TASK", "READY_TASK", "START_TASK", "REPORT_TASK",
    "RECORD_VERIFICATION", "WAIT_FOR_REVIEW", "RECORD_REVIEW", "ACCEPT_TASK",
    "RESOLVE_BLOCKER", "RECORD_DELIVERY", "COMPLETE_RUN", "CANCEL_TASK", "CANCEL_RUN",
)
_OUTCOMES = ("success", "denied", "provider_failure", "abandoned")
_DELIVERY_TARGETS = ("patch", "working_tree", "commit", "pr", "merge", "deploy")


class IntegrityError(ValueError):
    """Fail-closed error for corrupt or contradictory event history."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _strict_fields(raw: Any, fields: tuple[str, ...], label: str) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValidationError("INVALID_TYPE", f"{label} must be an object")
    raw = dict(raw)
    unknown = sorted(set(raw) - set(fields))
    missing = sorted(set(fields) - set(raw))
    if unknown:
        raise ValidationError("UNKNOWN_FIELD", f"{label} contains {unknown[0]!r}")
    if missing:
        raise ValidationError("MISSING_FIELD", f"{label} is missing {missing[0]!r}")
    return raw


def _strict_fields_optional(raw: Any, required: tuple[str, ...], optional: tuple[str, ...],
                            label: str) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValidationError("INVALID_TYPE", f"{label} must be an object")
    raw = dict(raw)
    unknown = sorted(set(raw) - set(required) - set(optional))
    missing = sorted(set(required) - set(raw))
    if unknown:
        raise ValidationError("UNKNOWN_FIELD", f"{label} contains {unknown[0]!r}")
    if missing:
        raise ValidationError("MISSING_FIELD", f"{label} is missing {missing[0]!r}")
    return raw


def _integer(value: Any, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError("INVALID_TYPE", f"{field} must be an integer")
    if value < minimum:
        raise ValidationError("INVALID_VALUE", f"{field} must be at least {minimum}")
    return value


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValidationError("INVALID_TYPE", f"{field} must be a string")
    if len(value) != len(_HASH_PREFIX) + 64 or not value.startswith(_HASH_PREFIX):
        raise ValidationError("INVALID_VALUE", f"{field} must be a sha256: digest")
    if any(character not in "0123456789abcdef" for character in value[len(_HASH_PREFIX):]):
        raise ValidationError("INVALID_VALUE", f"{field} must be a sha256: digest")
    return value


def _frozen_json_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError("INVALID_TYPE", f"{field} must be an object")
    try:
        normalized = json.loads(json.dumps(_plain(value), ensure_ascii=False, sort_keys=True,
                                           separators=(",", ":"), allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValidationError("INVALID_TYPE", f"{field} must be JSON-safe") from exc
    return _freeze(normalized)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValidationError("INVALID_TYPE", f"{field} must be a string")
    if not value:
        raise ValidationError("INVALID_VALUE", f"{field} must not be empty")
    return value


def _enum(value: Any, field: str, values: tuple[str, ...]) -> str:
    value = _string(value, field)
    if value not in values:
        raise ValidationError("UNKNOWN_ENUM", f"{field} has unsupported value {value!r}")
    return value


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError("INVALID_TYPE", f"{field} must be a boolean")
    return value


def _json_value(value: Any, field: str) -> Any:
    try:
        return _freeze(json.loads(json.dumps(_plain(value), ensure_ascii=False, sort_keys=True,
                                             separators=(",", ":"), allow_nan=False)))
    except (TypeError, ValueError) as exc:
        raise ValidationError("INVALID_TYPE", f"{field} must be JSON-safe") from exc


def _task_id_payload(raw: Any, event_type: str) -> dict[str, Any]:
    raw = _strict_fields(raw, ("task_id",), event_type)
    return {"task_id": validate_id(raw["task_id"], "task_id")}


def _digest_payload(value: Any, field: str) -> str:
    return _hash(value, field)


def _decode_event_payload(event_type: str, raw: Any) -> Mapping[str, Any]:
    if event_type == "REQUEST_RESERVED":
        raw = _strict_fields(raw, ("request_id", "request_sha256", "command_type",
                                   "reservation_sequence"), event_type)
        return {
            "request_id": validate_id(raw["request_id"], "request_id"),
            "request_sha256": _digest_payload(raw["request_sha256"], "request_sha256"),
            "command_type": _enum(raw["command_type"], "command_type", ("RECORD_VERIFICATION",)),
            "reservation_sequence": _integer(raw["reservation_sequence"], "reservation_sequence", 1),
        }
    if event_type == "REQUEST_RESOLVED":
        raw = _strict_fields(raw, ("request_id", "outcome", "reason_code", "result_summary",
                                   "event_ids", "request_sha256", "command_type", "expected_sequence"), event_type)
        reason_code = raw["reason_code"]
        if reason_code is not None:
            reason_code = validate_id(reason_code, "reason_code")
        summary = _frozen_json_mapping(raw["result_summary"], "result_summary")
        if not isinstance(raw["event_ids"], (list, tuple)):
            raise ValidationError("INVALID_TYPE", "event_ids must be a list")
        event_ids = tuple(validate_id(item, "event_ids[]") for item in raw["event_ids"])
        if len(set(event_ids)) != len(event_ids):
            raise ValidationError("DUPLICATE_VALUE", "event_ids contains a duplicate value")
        return {"request_id": validate_id(raw["request_id"], "request_id"),
                "request_sha256": _hash(raw["request_sha256"], "request_sha256"),
                "command_type": _enum(raw["command_type"], "command_type", _COMMAND_TYPES),
                "expected_sequence": _integer(raw["expected_sequence"], "expected_sequence"),
                "outcome": _enum(raw["outcome"], "outcome", _OUTCOMES),
                "reason_code": reason_code, "result_summary": summary, "event_ids": event_ids}
    if event_type == "RUN_CREATED":
        raw = _strict_fields(raw, ("work_id", "goal", "route"), event_type)
        goal = _string(raw["goal"], "goal")
        if not goal.strip():
            raise ValidationError("INVALID_VALUE", "goal must contain non-whitespace text")
        return {"work_id": validate_id(raw["work_id"], "work_id"), "goal": goal,
                "route": RouteContract.from_dict(_plain(raw["route"])).to_dict()}
    if event_type in ("RUN_BLOCKED", "RUN_RESUMED", "RUN_COMPLETED", "RUN_CANCELLED"):
        _strict_fields(raw, (), event_type)
        return {}
    if event_type == "TASK_ADDED":
        raw = _strict_fields(raw, ("task",), event_type)
        return {"task": TaskContract.from_dict(_plain(raw["task"])).to_dict()}
    if event_type == "TASK_STARTED":
        raw = _strict_fields(raw, ("task_id", "scope_origin"), event_type)
        return {"task_id": validate_id(raw["task_id"], "task_id"),
                "scope_origin": WorkspaceRevision.from_dict(_plain(raw["scope_origin"])).to_dict()}
    if event_type == "TASK_REPORTED":
        raw = _strict_fields(raw, ("task_id", "report"), event_type)
        report = _strict_fields(raw["report"], ("summary", "workspace_revision"), "report")
        return {"task_id": validate_id(raw["task_id"], "task_id"),
                "report": {"summary": _string(report["summary"], "report.summary"),
                           "workspace_revision": WorkspaceRevision.from_dict(_plain(report["workspace_revision"])).to_dict()}}
    if event_type == "VERIFICATION_RECORDED":
        raw = _strict_fields_optional(raw, ("task_id", "success"), ("evidence",), event_type)
        result = {"task_id": validate_id(raw["task_id"], "task_id"),
                  "success": _boolean(raw["success"], "success")}
        if "evidence" in raw:
            result["evidence"] = EvidenceRecord.from_dict(_plain(raw["evidence"])).to_dict()
        return result
    if event_type == "REVIEW_RECORDED":
        raw = _strict_fields_optional(raw, ("task_id", "verdict_fingerprint"), ("assertion",), event_type)
        result = {"task_id": validate_id(raw["task_id"], "task_id"),
                "verdict_fingerprint": _digest_payload(raw["verdict_fingerprint"],
                                                        "verdict_fingerprint")}
        if "assertion" in raw:
            result["assertion"] = ReviewAssertion.from_dict(_plain(raw["assertion"])).to_dict()
        return result
    if event_type == "TASK_ACCEPTED":
        raw = _strict_fields(raw, ("task_id", "input_fingerprint", "verdict_fingerprint"), event_type)
        return {"task_id": validate_id(raw["task_id"], "task_id"),
                "input_fingerprint": _digest_payload(raw["input_fingerprint"], "input_fingerprint"),
                "verdict_fingerprint": _digest_payload(raw["verdict_fingerprint"],
                                                        "verdict_fingerprint")}
    if event_type == "TASK_INVALIDATED":
        raw = _strict_fields(raw, ("task_id", "new_task_revision"), event_type)
        return {"task_id": validate_id(raw["task_id"], "task_id"),
                "new_task_revision": _integer(raw["new_task_revision"], "new_task_revision", 1)}
    if event_type == "DELIVERY_RECORDED":
        raw = _strict_fields(raw, ("delivery_target", "acceptance_set_sha256", "provenance",
                                  "workspace_revision"), event_type)
        provenance = _strict_fields(raw["provenance"], ("provider", "reference"), "provenance")
        result = {"delivery_target": _enum(raw["delivery_target"], "delivery_target", _DELIVERY_TARGETS),
                "acceptance_set_sha256": _digest_payload(raw["acceptance_set_sha256"],
                                                           "acceptance_set_sha256"),
                "provenance": {"provider": validate_id(provenance["provider"], "provenance.provider"),
                               "reference": _string(provenance["reference"], "provenance.reference")},
                "workspace_revision": WorkspaceRevision.from_dict(_plain(raw["workspace_revision"])).to_dict()}
        return result
    if event_type == "TASK_UNBLOCKED":
        raw = _strict_fields(raw, ("task_id", "provenance"), event_type)
        provenance = _strict_fields(raw["provenance"], ("actor", "resolution"), "provenance")
        return {"task_id": validate_id(raw["task_id"], "task_id"),
                "provenance": {"actor": validate_id(provenance["actor"], "provenance.actor"),
                               "resolution": _string(provenance["resolution"], "provenance.resolution")}}
    if event_type == "TASK_BLOCKED":
        raw = _strict_fields_optional(raw, ("task_id",), ("review_round",), event_type)
        result = {"task_id": validate_id(raw["task_id"], "task_id")}
        if "review_round" in raw:
            result["review_round"] = _integer(raw["review_round"], "review_round", 1)
        return result
    return _task_id_payload(raw, event_type)


def _utc_timestamp(value: Any) -> str:
    value = _string(value, "occurred_at")
    if not _UTC_TIMESTAMP.fullmatch(value):
        raise ValidationError("INVALID_VALUE", "occurred_at must be an ISO-8601 UTC timestamp")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValidationError("INVALID_VALUE", "occurred_at must be an ISO-8601 UTC timestamp") from exc
    return value


def _actor(value: Any) -> Mapping[str, Any]:
    raw = _strict_fields(value, ("type", "id"), "actor")
    return MappingProxyType({"type": validate_id(raw["type"], "actor.type"),
                             "id": validate_id(raw["id"], "actor.id")})


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    payload: Mapping[str, Any]

    _FIELDS: ClassVar[tuple[str, ...]] = ("event_type", "payload")

    def __post_init__(self) -> None:
        event_type = validate_id(self.event_type, "event_type")
        if event_type not in _EVENT_TYPES:
            raise ValidationError("UNKNOWN_ENUM", f"event_type has unsupported value {event_type!r}")
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "payload", _frozen_json_mapping(
            _decode_event_payload(event_type, self.payload), "payload"))

    @classmethod
    def from_dict(cls, raw: Any) -> "DomainEvent":
        raw = _strict_fields(raw, cls._FIELDS, "DomainEvent")
        return cls(event_type=raw["event_type"], payload=raw["payload"])

    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, "payload": _plain(self.payload)}


@dataclass(frozen=True)
class EventBatch:
    schema_version: int
    sequence: int
    batch_id: str
    request_id: str
    request_sha256: str
    work_id: str
    occurred_at: str
    actor: Mapping[str, Any]
    previous_hash: str
    events: tuple[DomainEvent, ...]
    batch_hash: str

    _FIELDS: ClassVar[tuple[str, ...]] = (
        "schema_version", "sequence", "batch_id", "request_id", "request_sha256", "work_id",
        "occurred_at", "actor", "previous_hash", "events", "batch_hash")

    def __post_init__(self) -> None:
        if (isinstance(self.schema_version, bool) or not isinstance(self.schema_version, int)
                or self.schema_version != 1):
            raise ValidationError("UNKNOWN_SCHEMA_VERSION", "schema_version 1 is required")
        object.__setattr__(self, "sequence", _integer(self.sequence, "sequence", 1))
        object.__setattr__(self, "batch_id", validate_id(self.batch_id, "batch_id"))
        object.__setattr__(self, "request_id", validate_id(self.request_id, "request_id"))
        object.__setattr__(self, "request_sha256", _hash(self.request_sha256, "request_sha256"))
        object.__setattr__(self, "work_id", validate_id(self.work_id, "work_id"))
        object.__setattr__(self, "occurred_at", _utc_timestamp(self.occurred_at))
        object.__setattr__(self, "actor", _actor(self.actor))
        object.__setattr__(self, "previous_hash", _hash(self.previous_hash, "previous_hash"))
        if not isinstance(self.events, (list, tuple)) or not self.events:
            raise ValidationError("INVALID_VALUE", "events must be a non-empty list")
        normalized_events = tuple(
            DomainEvent(item.event_type, item.payload) if isinstance(item, DomainEvent)
            else DomainEvent.from_dict(item)
            for item in self.events
        )
        object.__setattr__(self, "events", normalized_events)
        object.__setattr__(self, "batch_hash", _hash(self.batch_hash, "batch_hash"))

    @classmethod
    def create(cls, *, sequence: int, batch_id: str, request_id: str, request_sha256: str,
               work_id: str, occurred_at: str, actor: Mapping[str, Any], previous_hash: str,
               events: list[DomainEvent] | tuple[DomainEvent, ...]) -> "EventBatch":
        provisional = {
            "schema_version": 1, "sequence": sequence, "batch_id": batch_id,
            "request_id": request_id, "request_sha256": request_sha256, "work_id": work_id,
            "occurred_at": occurred_at, "actor": _plain(actor), "previous_hash": previous_hash,
            "events": [item.to_dict() if isinstance(item, DomainEvent) else item for item in events],
        }
        return cls.from_dict({**provisional, "batch_hash": canonical_sha256(provisional)})

    @classmethod
    def from_dict(cls, raw: Any) -> "EventBatch":
        raw = _strict_fields(raw, cls._FIELDS, "EventBatch")
        events_raw = raw["events"]
        if not isinstance(events_raw, list):
            raise ValidationError("INVALID_TYPE", "events must be a list")
        return cls(
            schema_version=raw["schema_version"], sequence=raw["sequence"], batch_id=raw["batch_id"],
            request_id=raw["request_id"], request_sha256=raw["request_sha256"], work_id=raw["work_id"],
            occurred_at=raw["occurred_at"], actor=raw["actor"], previous_hash=raw["previous_hash"],
            events=events_raw, batch_hash=raw["batch_hash"],
        )

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "sequence": self.sequence,
            "batch_id": self.batch_id, "request_id": self.request_id,
            "request_sha256": self.request_sha256, "work_id": self.work_id,
            "occurred_at": self.occurred_at, "actor": _plain(self.actor),
            "previous_hash": self.previous_hash,
            "events": [event.to_dict() for event in self.events],
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "batch_hash": self.batch_hash}


def verify_batch(previous: EventBatch | None, batch: EventBatch) -> None:
    """Verify one batch against its predecessor without mutating either value."""
    expected_sequence = 1 if previous is None else previous.sequence + 1
    expected_previous_hash = ZERO_HASH if previous is None else previous.batch_hash
    if batch.sequence != expected_sequence:
        raise IntegrityError("EVENT_SEQUENCE_MISMATCH", "batch sequence is not continuous")
    if batch.previous_hash != expected_previous_hash:
        raise IntegrityError("EVENT_HASH_MISMATCH", "previous hash does not match")
    if batch.batch_hash != canonical_sha256(batch.unsigned_dict()):
        raise IntegrityError("EVENT_HASH_MISMATCH", "batch hash does not match its contents")
    for event in batch.events:
        if event.event_type in ("REQUEST_RESERVED", "REQUEST_RESOLVED"):
            if (event.payload["request_id"], event.payload["request_sha256"]) != (batch.request_id, batch.request_sha256):
                raise IntegrityError("REQUEST_CONFLICT", "request identity does not match its batch")
            if event.event_type == "REQUEST_RESERVED" and event.payload["reservation_sequence"] != batch.sequence:
                raise IntegrityError("REQUEST_CONFLICT", "reservation sequence does not match its batch")
