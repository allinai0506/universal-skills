"""Immutable, hash-chained workflow event envelopes."""
from __future__ import annotations

from dataclasses import dataclass
import json
from types import MappingProxyType
from typing import Any, ClassVar, Mapping

from .model import ValidationError, canonical_sha256, validate_id


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


class IntegrityError(ValueError):
    """Fail-closed error for corrupt or contradictory event history."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _strict_fields(raw: Any, fields: tuple[str, ...], label: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValidationError("INVALID_TYPE", f"{label} must be an object")
    unknown = sorted(set(raw) - set(fields))
    missing = sorted(set(fields) - set(raw))
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
        normalized = json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True,
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


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    payload: Mapping[str, Any]

    _FIELDS: ClassVar[tuple[str, ...]] = ("event_type", "payload")

    @classmethod
    def from_dict(cls, raw: Any) -> "DomainEvent":
        raw = _strict_fields(raw, cls._FIELDS, "DomainEvent")
        event_type = validate_id(raw["event_type"], "event_type")
        if event_type not in _EVENT_TYPES:
            raise ValidationError("UNKNOWN_ENUM", f"event_type has unsupported value {event_type!r}")
        return cls(event_type=event_type, payload=_frozen_json_mapping(raw["payload"], "payload"))

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
        if (isinstance(raw["schema_version"], bool) or not isinstance(raw["schema_version"], int)
                or raw["schema_version"] != 1):
            raise ValidationError("UNKNOWN_SCHEMA_VERSION", "schema_version 1 is required")
        events_raw = raw["events"]
        if not isinstance(events_raw, list) or not events_raw:
            raise ValidationError("INVALID_VALUE", "events must be a non-empty list")
        events = tuple(DomainEvent.from_dict(item) for item in events_raw)
        if not isinstance(raw["occurred_at"], str) or not raw["occurred_at"]:
            raise ValidationError("INVALID_TYPE", "occurred_at must be a non-empty string")
        return cls(
            schema_version=1, sequence=_integer(raw["sequence"], "sequence", 1),
            batch_id=validate_id(raw["batch_id"], "batch_id"),
            request_id=validate_id(raw["request_id"], "request_id"),
            request_sha256=_hash(raw["request_sha256"], "request_sha256"),
            work_id=validate_id(raw["work_id"], "work_id"), occurred_at=raw["occurred_at"],
            actor=_frozen_json_mapping(raw["actor"], "actor"),
            previous_hash=_hash(raw["previous_hash"], "previous_hash"), events=events,
            batch_hash=_hash(raw["batch_hash"], "batch_hash"),
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
