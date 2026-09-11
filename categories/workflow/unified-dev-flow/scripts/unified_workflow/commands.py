"""Strict command and gate-decision values."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping

from .model import (_expect_fields, _integer, _json_plain, _json_safe, _schema_version,
                    _unique_strings, validate_id, ValidationError)


_COMMAND_TYPES = (
    "INIT_RUN", "ADD_TASK", "READY_TASK", "START_TASK", "REPORT_TASK",
    "RECORD_VERIFICATION", "WAIT_FOR_REVIEW", "RECORD_REVIEW", "ACCEPT_TASK",
    "RESOLVE_BLOCKER", "RECORD_DELIVERY", "COMPLETE_RUN", "CANCEL_TASK", "CANCEL_RUN",
)


@dataclass(frozen=True)
class Command:
    schema_version: int
    request_id: str
    command_type: str
    work_id: str
    task_id: str | None
    actor: Mapping[str, Any]
    expected_sequence: int
    payload: Mapping[str, Any]

    _FIELDS: ClassVar[tuple[str, ...]] = (
        "schema_version", "request_id", "command_type", "work_id", "task_id", "actor",
        "expected_sequence", "payload")

    @classmethod
    def from_dict(cls, raw: Any) -> "Command":
        raw = _expect_fields(raw, cls._FIELDS, "Command")
        task_id = raw["task_id"]
        if task_id is not None:
            task_id = validate_id(task_id, "task_id")
        actor = _json_safe(raw["actor"], "actor")
        payload = _json_safe(raw["payload"], "payload")
        if not isinstance(actor, Mapping) or not isinstance(payload, Mapping):
            raise ValidationError("INVALID_TYPE", "actor and payload must be mappings")
        return cls(
            schema_version=_schema_version(raw["schema_version"]),
            request_id=validate_id(raw["request_id"], "request_id"),
            command_type=_command_type(raw["command_type"]),
            work_id=validate_id(raw["work_id"], "work_id"), task_id=task_id, actor=actor,
            expected_sequence=_integer(raw["expected_sequence"], "expected_sequence", minimum=0),
            payload=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "request_id": self.request_id,
                "command_type": self.command_type, "work_id": self.work_id,
                "task_id": self.task_id, "actor": _json_plain(self.actor),
                "expected_sequence": self.expected_sequence, "payload": _json_plain(self.payload)}


@dataclass(frozen=True)
class Allowed:
    result: Any

    _FIELDS: ClassVar[tuple[str, ...]] = ("result",)

    @classmethod
    def from_dict(cls, raw: Any) -> "Allowed":
        raw = _expect_fields(raw, cls._FIELDS, "Allowed")
        return cls(result=_json_safe(raw["result"], "result"))

    def to_dict(self) -> dict[str, Any]:
        return {"result": _json_plain(self.result)}


@dataclass(frozen=True)
class Denied:
    reason_code: str
    required_actions: tuple[str, ...]

    _FIELDS: ClassVar[tuple[str, ...]] = ("reason_code", "required_actions")

    @classmethod
    def from_dict(cls, raw: Any) -> "Denied":
        raw = _expect_fields(raw, cls._FIELDS, "Denied")
        return cls(reason_code=validate_id(raw["reason_code"], "reason_code"),
                   required_actions=_unique_strings(raw["required_actions"], "required_actions"))

    def to_dict(self) -> dict[str, Any]:
        return {"reason_code": self.reason_code, "required_actions": list(self.required_actions)}


@dataclass(frozen=True)
class Decision:
    events: tuple[Any, ...]
    outcome: Allowed | Denied

    _FIELDS: ClassVar[tuple[str, ...]] = ("events", "outcome")

    @classmethod
    def from_dict(cls, raw: Any) -> "Decision":
        raw = _expect_fields(raw, cls._FIELDS, "Decision")
        if not isinstance(raw["events"], list):
            raise ValidationError("INVALID_TYPE", "events must be a list")
        outcome = raw["outcome"]
        if not isinstance(outcome, dict):
            raise ValidationError("INVALID_TYPE", "outcome must be an object")
        kind = outcome.get("kind")
        if kind == "allowed":
            allowed = {key: value for key, value in outcome.items() if key != "kind"}
            parsed: Allowed | Denied = Allowed.from_dict(allowed)
        elif kind == "denied":
            denied = {key: value for key, value in outcome.items() if key != "kind"}
            parsed = Denied.from_dict(denied)
        else:
            raise ValidationError("UNKNOWN_ENUM", "outcome.kind must be allowed or denied")
        return cls(events=tuple(_json_safe(event, "events[]") for event in raw["events"]), outcome=parsed)

    def to_dict(self) -> dict[str, Any]:
        if isinstance(self.outcome, Allowed):
            outcome = {"kind": "allowed", **self.outcome.to_dict()}
        else:
            outcome = {"kind": "denied", **self.outcome.to_dict()}
        return {"events": [_json_plain(event) for event in self.events], "outcome": outcome}


def _command_type(value: Any) -> str:
    value = validate_id(value, "command_type")
    if value not in _COMMAND_TYPES:
        raise ValidationError("UNKNOWN_ENUM", f"command_type has unsupported value {value!r}")
    return value
