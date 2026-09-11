"""Strict, immutable protocol values for the Unified Workflow kernel."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path, PurePosixPath
import re
from types import MappingProxyType
from typing import Any, ClassVar, Mapping


DELIVERY_ORDER = ("patch", "working_tree", "commit", "pr", "merge", "deploy")
OUTCOMES = ("success", "denied", "provider_failure", "abandoned")
VERDICTS = ("MERGE_READY", "NEEDS_FIXES", "ESCALATE")
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CONTROL_PREFIXES = (".git", ".unified-dev-flow")
REVIEW_PROVENANCE = ("cross_model", "human", "mock")

_RESUMES = ("fresh", "match", "compatible_drift", "conflicting_drift")
_INTENTS = ("bug", "feature", "refactor", "migration", "research", "config")
_COMPLEXITIES = ("micro", "small", "medium", "large", "intractable")
_RISKS = ("auth", "permission", "security", "money", "data_integrity", "production",
          "state_machine", "concurrency", "migration")
_DOMAINS = ("ui", "api", "database", "performance", "docs", "infrastructure")
_SPEC_BACKENDS = ("unified", "speckit", "openspec")
_ASSURANCE_LEVELS = ("deterministic", "adversarial", "mutation")
_PROOF_MODES = ("acceptance_test", "failing_test", "stable_reproduction",
                "characterization", "dry_run", "benchmark", "exploit", "schema_lint",
                "visual_e2e")
_REQUIRED_REVIEWS = ("none", "provenance_assertion")
_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class ValidationError(ValueError):
    """A fail-closed schema or value validation error."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _error(code: str, message: str) -> None:
    raise ValidationError(code, message)


def _expect_fields(raw: Any, fields: tuple[str, ...], label: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        _error("INVALID_TYPE", f"{label} must be an object")
    actual = set(raw)
    expected = set(fields)
    unknown = sorted(actual - expected)
    if unknown:
        _error("UNKNOWN_FIELD", f"{label} contains {unknown[0]!r}")
    missing = sorted(expected - actual)
    if missing:
        _error("MISSING_FIELD", f"{label} is missing {missing[0]!r}")
    return raw


def _string(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        _error("INVALID_TYPE", f"{field} must be a string")
    if not allow_empty and not value:
        _error("INVALID_VALUE", f"{field} must not be empty")
    return value


def _integer(value: Any, field: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _error("INVALID_TYPE", f"{field} must be an integer")
    if minimum is not None and value < minimum:
        _error("INVALID_VALUE", f"{field} must be at least {minimum}")
    return value


def _schema_version(value: Any) -> int:
    version = _integer(value, "schema_version")
    if version != 1:
        _error("UNKNOWN_SCHEMA_VERSION", f"schema_version {version!r} is unsupported")
    return version


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        _error("INVALID_TYPE", f"{field} must be a boolean")
    return value


def _enum(value: Any, field: str, values: tuple[str, ...]) -> str:
    value = _string(value, field)
    if value not in values:
        _error("UNKNOWN_ENUM", f"{field} has unsupported value {value!r}")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _string(value, field)
    if not _SHA256_PATTERN.fullmatch(value):
        _error("INVALID_VALUE", f"{field} must be a sha256: digest")
    return value


def validate_id(value: Any, field: str) -> str:
    value = _string(value, field)
    if not ID_PATTERN.fullmatch(value):
        _error("INVALID_ID", f"{field} is not a valid identifier")
    return value


def _relative_path(value: Any, field: str, *, allow_dot: bool = False,
                   allow_control: bool = False) -> str:
    value = _string(value, field)
    if "\\" in value:
        _error("INVALID_PATH", f"{field} must use POSIX separators")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or (value == "." and not allow_dot):
        _error("INVALID_PATH", f"{field} must be a safe relative path")
    if not allow_control and path.parts and path.parts[0] in CONTROL_PREFIXES:
        _error("CONTROL_PATH", f"{field} must not address a control directory")
    return value


def resolve_project_path(root: Path, value: Any, field: str) -> Path:
    """Resolve an existing or prospective relative path without symlink escape."""
    relative = _relative_path(value, field, allow_dot=True, allow_control=False)
    try:
        project_root = Path(root).resolve(strict=True)
    except OSError as exc:
        _error("INVALID_PATH", f"{field} root cannot be resolved: {exc}")
    if not project_root.is_dir():
        _error("INVALID_PATH", f"{field} root is not a directory")
    try:
        resolved = (project_root / relative).resolve(strict=False)
        resolved.relative_to(project_root)
    except (OSError, ValueError):
        _error("PATH_ESCAPE", f"{field} resolves outside the project root")
    for prefix in CONTROL_PREFIXES:
        control_root = (project_root / prefix).resolve(strict=False)
        try:
            resolved.relative_to(control_root)
        except ValueError:
            continue
        _error("CONTROL_PATH", f"{field} resolves into a control directory")
    return resolved


def _json_safe(value: Any, field: str = "value") -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            _error("INVALID_VALUE", f"{field} must not contain non-finite floats")
        return value
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, nested in value.items():
            if not isinstance(key, str):
                _error("INVALID_TYPE", f"{field} mapping keys must be strings")
            copied[key] = _json_safe(nested, f"{field}.{key}")
        return MappingProxyType(copied)
    if isinstance(value, (list, tuple)):
        copied = tuple(_json_safe(nested, f"{field}[]") for nested in value)
        encoded = [json.dumps(_json_plain(item), ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False) for item in copied]
        if len(set(encoded)) != len(encoded):
            _error("DUPLICATE_VALUE", f"{field} contains a duplicate value")
        return copied
    _error("INVALID_TYPE", f"{field} must be JSON-safe")


def _json_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_plain(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_json_plain(nested) for nested in value]
    if isinstance(value, list):
        return [_json_plain(nested) for nested in value]
    return value


def canonical_json(value: Any) -> str:
    """Return a deterministic JSON serialization after validating JSON safety."""
    return json.dumps(_json_plain(_json_safe(value)), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def canonical_sha256(value: Any) -> str:
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _unique_strings(value: Any, field: str, *, values: tuple[str, ...] | None = None,
                    ids: bool = False, paths: bool = False, allow_dot: bool = False,
                    allow_control: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        _error("INVALID_TYPE", f"{field} must be a list")
    parsed: list[str] = []
    for item in value:
        if values is not None:
            parsed.append(_enum(item, f"{field}[]", values))
        elif ids:
            parsed.append(validate_id(item, f"{field}[]"))
        elif paths:
            parsed.append(_relative_path(item, f"{field}[]", allow_dot=allow_dot,
                                         allow_control=allow_control))
        else:
            parsed.append(_string(item, f"{field}[]"))
    if len(set(parsed)) != len(parsed):
        _error("DUPLICATE_VALUE", f"{field} contains a duplicate value")
    return tuple(parsed)


@dataclass(frozen=True)
class RouteObligations:
    verification_claims: tuple[str, ...]
    accepted_review_provenance: tuple[str, ...]
    required_delivery: str

    _FIELDS: ClassVar[tuple[str, ...]] = (
        "verification_claims", "accepted_review_provenance", "required_delivery")

    @classmethod
    def from_dict(cls, raw: Any) -> "RouteObligations":
        raw = _expect_fields(raw, cls._FIELDS, "RouteObligations")
        return cls(
            verification_claims=_unique_strings(raw["verification_claims"], "verification_claims",
                                                values=_ASSURANCE_LEVELS),
            accepted_review_provenance=_unique_strings(
                raw["accepted_review_provenance"], "accepted_review_provenance",
                values=REVIEW_PROVENANCE),
            required_delivery=_enum(raw["required_delivery"], "required_delivery", DELIVERY_ORDER),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"verification_claims": list(self.verification_claims),
                "accepted_review_provenance": list(self.accepted_review_provenance),
                "required_delivery": self.required_delivery}


@dataclass(frozen=True)
class RouteContract:
    schema_version: int
    resume: str
    intent: str
    complexity: str
    risks: tuple[str, ...]
    domains: tuple[str, ...]
    delivery_target: str
    spec_backend: str
    controller: str | None
    proof_mode: str
    assurance_level: str
    review_limit: int
    obligations: RouteObligations
    source: Mapping[str, Any]

    _FIELDS: ClassVar[tuple[str, ...]] = (
        "schema_version", "resume", "intent", "complexity", "risks", "domains",
        "delivery_target", "spec_backend", "controller", "proof_mode", "assurance_level",
        "review_limit", "obligations", "source")

    @classmethod
    def from_dict(cls, raw: Any) -> "RouteContract":
        raw = _expect_fields(raw, cls._FIELDS, "RouteContract")
        source = _expect_fields(raw["source"], ("policy_version", "policy_sha256"), "source")
        controller = raw["controller"]
        if controller is not None:
            controller = validate_id(controller, "controller")
        return cls(
            schema_version=_schema_version(raw["schema_version"]),
            resume=_enum(raw["resume"], "resume", _RESUMES),
            intent=_enum(raw["intent"], "intent", _INTENTS),
            complexity=_enum(raw["complexity"], "complexity", _COMPLEXITIES),
            risks=_unique_strings(raw["risks"], "risks", values=_RISKS),
            domains=_unique_strings(raw["domains"], "domains", values=_DOMAINS),
            delivery_target=_enum(raw["delivery_target"], "delivery_target", DELIVERY_ORDER),
            spec_backend=_enum(raw["spec_backend"], "spec_backend", _SPEC_BACKENDS),
            controller=controller,
            proof_mode=_enum(raw["proof_mode"], "proof_mode", _PROOF_MODES),
            assurance_level=_enum(raw["assurance_level"], "assurance_level", _ASSURANCE_LEVELS),
            review_limit=_integer(raw["review_limit"], "review_limit", minimum=0),
            obligations=RouteObligations.from_dict(raw["obligations"]),
            source=MappingProxyType({
                "policy_version": _string(source["policy_version"], "source.policy_version"),
                "policy_sha256": _sha256(source["policy_sha256"], "source.policy_sha256"),
            }),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "resume": self.resume,
                "intent": self.intent, "complexity": self.complexity, "risks": list(self.risks),
                "domains": list(self.domains), "delivery_target": self.delivery_target,
                "spec_backend": self.spec_backend, "controller": self.controller,
                "proof_mode": self.proof_mode, "assurance_level": self.assurance_level,
                "review_limit": self.review_limit, "obligations": self.obligations.to_dict(),
                "source": _json_plain(self.source)}


@dataclass(frozen=True)
class WriteScope:
    allowed_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]

    _FIELDS: ClassVar[tuple[str, ...]] = ("allowed_paths", "forbidden_paths")

    @classmethod
    def from_dict(cls, raw: Any) -> "WriteScope":
        raw = _expect_fields(raw, cls._FIELDS, "WriteScope")
        allowed = _unique_strings(raw["allowed_paths"], "allowed_paths", paths=True)
        if not allowed:
            _error("INVALID_VALUE", "allowed_paths must not be empty for a writable task")
        forbidden = _unique_strings(raw["forbidden_paths"], "forbidden_paths", paths=True,
                                    allow_control=True)
        return cls(allowed_paths=allowed, forbidden_paths=forbidden)

    def to_dict(self) -> dict[str, Any]:
        return {"allowed_paths": list(self.allowed_paths), "forbidden_paths": list(self.forbidden_paths)}


@dataclass(frozen=True)
class VerificationCommand:
    command_id: str
    argv: tuple[str, ...]
    cwd: str
    timeout_seconds: int
    max_output_bytes: int
    required: bool
    claims: tuple[str, ...]

    _FIELDS: ClassVar[tuple[str, ...]] = (
        "command_id", "argv", "cwd", "timeout_seconds", "max_output_bytes", "required", "claims")

    @classmethod
    def from_dict(cls, raw: Any) -> "VerificationCommand":
        raw = _expect_fields(raw, cls._FIELDS, "VerificationCommand")
        argv = _unique_strings(raw["argv"], "argv")
        if not argv:
            _error("INVALID_VALUE", "argv must not be empty")
        return cls(
            command_id=validate_id(raw["command_id"], "command_id"), argv=argv,
            cwd=_relative_path(raw["cwd"], "cwd", allow_dot=True),
            timeout_seconds=_integer(raw["timeout_seconds"], "timeout_seconds", minimum=1),
            max_output_bytes=_integer(raw["max_output_bytes"], "max_output_bytes", minimum=1),
            required=_boolean(raw["required"], "required"),
            claims=_unique_strings(raw["claims"], "claims", values=_ASSURANCE_LEVELS),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"command_id": self.command_id, "argv": list(self.argv), "cwd": self.cwd,
                "timeout_seconds": self.timeout_seconds, "max_output_bytes": self.max_output_bytes,
                "required": self.required, "claims": list(self.claims)}


@dataclass(frozen=True)
class TaskContract:
    schema_version: int
    task_id: str
    objective: str
    required: bool
    dependencies: tuple[str, ...]
    write_scope: WriteScope
    verification_inputs: tuple[str, ...]
    acceptance: tuple[str, ...]
    verification_commands: tuple[VerificationCommand, ...]
    proof_mode: str
    required_review: str

    _FIELDS: ClassVar[tuple[str, ...]] = (
        "schema_version", "task_id", "objective", "required", "dependencies", "write_scope",
        "verification_inputs", "acceptance", "verification_commands", "proof_mode", "required_review")

    @classmethod
    def from_dict(cls, raw: Any) -> "TaskContract":
        raw = _expect_fields(raw, cls._FIELDS, "TaskContract")
        commands_raw = raw["verification_commands"]
        if not isinstance(commands_raw, list):
            _error("INVALID_TYPE", "verification_commands must be a list")
        commands = tuple(VerificationCommand.from_dict(item) for item in commands_raw)
        command_ids = [command.command_id for command in commands]
        if len(set(command_ids)) != len(command_ids):
            _error("DUPLICATE_VALUE", "verification_commands contains a duplicate command_id")
        acceptance = _unique_strings(raw["acceptance"], "acceptance")
        if not acceptance:
            _error("INVALID_VALUE", "acceptance must not be empty")
        return cls(
            schema_version=_schema_version(raw["schema_version"]),
            task_id=validate_id(raw["task_id"], "task_id"),
            objective=_string(raw["objective"], "objective"),
            required=_boolean(raw["required"], "required"),
            dependencies=_unique_strings(raw["dependencies"], "dependencies", ids=True),
            write_scope=WriteScope.from_dict(raw["write_scope"]),
            verification_inputs=_unique_strings(raw["verification_inputs"], "verification_inputs", paths=True),
            acceptance=acceptance,
            verification_commands=commands,
            proof_mode=_enum(raw["proof_mode"], "proof_mode", _PROOF_MODES),
            required_review=_enum(raw["required_review"], "required_review", _REQUIRED_REVIEWS),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "task_id": self.task_id,
                "objective": self.objective, "required": self.required,
                "dependencies": list(self.dependencies), "write_scope": self.write_scope.to_dict(),
                "verification_inputs": list(self.verification_inputs), "acceptance": list(self.acceptance),
                "verification_commands": [command.to_dict() for command in self.verification_commands],
                "proof_mode": self.proof_mode, "required_review": self.required_review}


@dataclass(frozen=True)
class WorkspaceRevision:
    schema_version: int
    provider: str
    revision_id: str
    verification_input_fingerprint: str
    changed_paths: tuple[str, ...]
    observed_at: str

    _FIELDS: ClassVar[tuple[str, ...]] = (
        "schema_version", "provider", "revision_id", "verification_input_fingerprint",
        "changed_paths", "observed_at")

    @classmethod
    def from_dict(cls, raw: Any) -> "WorkspaceRevision":
        raw = _expect_fields(raw, cls._FIELDS, "WorkspaceRevision")
        return cls(
            schema_version=_schema_version(raw["schema_version"]),
            provider=validate_id(raw["provider"], "provider"),
            revision_id=validate_id(raw["revision_id"], "revision_id"),
            verification_input_fingerprint=_sha256(
                raw["verification_input_fingerprint"], "verification_input_fingerprint"),
            changed_paths=_unique_strings(raw["changed_paths"], "changed_paths", paths=True),
            observed_at=_string(raw["observed_at"], "observed_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "provider": self.provider,
                "revision_id": self.revision_id,
                "verification_input_fingerprint": self.verification_input_fingerprint,
                "changed_paths": list(self.changed_paths), "observed_at": self.observed_at}


@dataclass(frozen=True)
class EvidenceRecord:
    schema_version: int
    task_id: str
    task_revision: int
    task_contract_sha256: str
    command_id: str
    command_sha256: str
    provider: str
    provider_version: str
    pre_command_revision: WorkspaceRevision
    post_command_revision: WorkspaceRevision
    commit_revision: WorkspaceRevision | None
    started_at: str
    ended_at: str
    exit_code: int | None
    timed_out: bool
    output_truncated: bool
    stdout_bytes: int
    stdout_sha256: str
    stdout_blob_ref: str | None
    stderr_bytes: int
    stderr_sha256: str
    stderr_blob_ref: str | None
    scope_diff: tuple[str, ...]
    verification_input_fingerprint: str
    evidence_sha256: str

    _FIELDS: ClassVar[tuple[str, ...]] = (
        "schema_version", "task_id", "task_revision", "task_contract_sha256", "command_id",
        "command_sha256", "provider", "provider_version", "pre_command_revision",
        "post_command_revision", "commit_revision", "started_at", "ended_at", "exit_code",
        "timed_out", "output_truncated", "stdout_bytes", "stdout_sha256", "stdout_blob_ref",
        "stderr_bytes", "stderr_sha256", "stderr_blob_ref", "scope_diff",
        "verification_input_fingerprint", "evidence_sha256")

    @classmethod
    def from_dict(cls, raw: Any) -> "EvidenceRecord":
        raw = _expect_fields(raw, cls._FIELDS, "EvidenceRecord")
        exit_code = raw["exit_code"]
        if exit_code is not None:
            exit_code = _integer(exit_code, "exit_code")
        commit_revision = raw["commit_revision"]
        if commit_revision is not None:
            commit_revision = WorkspaceRevision.from_dict(commit_revision)
        for field in ("stdout_blob_ref", "stderr_blob_ref"):
            if raw[field] is not None:
                _string(raw[field], field)
        return cls(
            schema_version=_schema_version(raw["schema_version"]),
            task_id=validate_id(raw["task_id"], "task_id"),
            task_revision=_integer(raw["task_revision"], "task_revision", minimum=1),
            task_contract_sha256=_sha256(raw["task_contract_sha256"], "task_contract_sha256"),
            command_id=validate_id(raw["command_id"], "command_id"),
            command_sha256=_sha256(raw["command_sha256"], "command_sha256"),
            provider=validate_id(raw["provider"], "provider"),
            provider_version=_string(raw["provider_version"], "provider_version"),
            pre_command_revision=WorkspaceRevision.from_dict(raw["pre_command_revision"]),
            post_command_revision=WorkspaceRevision.from_dict(raw["post_command_revision"]),
            commit_revision=commit_revision, started_at=_string(raw["started_at"], "started_at"),
            ended_at=_string(raw["ended_at"], "ended_at"), exit_code=exit_code,
            timed_out=_boolean(raw["timed_out"], "timed_out"),
            output_truncated=_boolean(raw["output_truncated"], "output_truncated"),
            stdout_bytes=_integer(raw["stdout_bytes"], "stdout_bytes", minimum=0),
            stdout_sha256=_sha256(raw["stdout_sha256"], "stdout_sha256"),
            stdout_blob_ref=raw["stdout_blob_ref"],
            stderr_bytes=_integer(raw["stderr_bytes"], "stderr_bytes", minimum=0),
            stderr_sha256=_sha256(raw["stderr_sha256"], "stderr_sha256"),
            stderr_blob_ref=raw["stderr_blob_ref"],
            scope_diff=_unique_strings(raw["scope_diff"], "scope_diff", paths=True),
            verification_input_fingerprint=_sha256(
                raw["verification_input_fingerprint"], "verification_input_fingerprint"),
            evidence_sha256=_sha256(raw["evidence_sha256"], "evidence_sha256"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "task_id": self.task_id,
            "task_revision": self.task_revision, "task_contract_sha256": self.task_contract_sha256,
            "command_id": self.command_id, "command_sha256": self.command_sha256,
            "provider": self.provider, "provider_version": self.provider_version,
            "pre_command_revision": self.pre_command_revision.to_dict(),
            "post_command_revision": self.post_command_revision.to_dict(),
            "commit_revision": None if self.commit_revision is None else self.commit_revision.to_dict(),
            "started_at": self.started_at, "ended_at": self.ended_at, "exit_code": self.exit_code,
            "timed_out": self.timed_out, "output_truncated": self.output_truncated,
            "stdout_bytes": self.stdout_bytes, "stdout_sha256": self.stdout_sha256,
            "stdout_blob_ref": self.stdout_blob_ref, "stderr_bytes": self.stderr_bytes,
            "stderr_sha256": self.stderr_sha256, "stderr_blob_ref": self.stderr_blob_ref,
            "scope_diff": list(self.scope_diff),
            "verification_input_fingerprint": self.verification_input_fingerprint,
            "evidence_sha256": self.evidence_sha256,
        }


@dataclass(frozen=True)
class ReviewAssertion:
    schema_version: int
    task_id: str
    task_revision: int
    reviewer: str
    provider: str
    provenance: str
    task_contract_sha256: str
    source_fingerprint: str
    test_fingerprint: str
    evidence_fingerprint: str
    verdict: str
    findings: tuple[Any, ...]
    reviewed_at: str
    assertion_sha256: str

    _FIELDS: ClassVar[tuple[str, ...]] = (
        "schema_version", "task_id", "task_revision", "reviewer", "provider", "provenance",
        "task_contract_sha256", "source_fingerprint", "test_fingerprint", "evidence_fingerprint",
        "verdict", "findings", "reviewed_at", "assertion_sha256")

    @classmethod
    def from_dict(cls, raw: Any) -> "ReviewAssertion":
        raw = _expect_fields(raw, cls._FIELDS, "ReviewAssertion")
        findings = raw["findings"]
        if not isinstance(findings, list):
            _error("INVALID_TYPE", "findings must be a list")
        frozen_findings = tuple(_json_safe(item, "findings[]") for item in findings)
        if len({canonical_json(item) for item in frozen_findings}) != len(frozen_findings):
            _error("DUPLICATE_VALUE", "findings contains a duplicate value")
        return cls(
            schema_version=_schema_version(raw["schema_version"]),
            task_id=validate_id(raw["task_id"], "task_id"),
            task_revision=_integer(raw["task_revision"], "task_revision", minimum=1),
            reviewer=validate_id(raw["reviewer"], "reviewer"),
            provider=validate_id(raw["provider"], "provider"),
            provenance=_enum(raw["provenance"], "provenance", REVIEW_PROVENANCE),
            task_contract_sha256=_sha256(raw["task_contract_sha256"], "task_contract_sha256"),
            source_fingerprint=_sha256(raw["source_fingerprint"], "source_fingerprint"),
            test_fingerprint=_sha256(raw["test_fingerprint"], "test_fingerprint"),
            evidence_fingerprint=_sha256(raw["evidence_fingerprint"], "evidence_fingerprint"),
            verdict=_enum(raw["verdict"], "verdict", VERDICTS), findings=frozen_findings,
            reviewed_at=_string(raw["reviewed_at"], "reviewed_at"),
            assertion_sha256=_sha256(raw["assertion_sha256"], "assertion_sha256"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "task_id": self.task_id,
            "task_revision": self.task_revision, "reviewer": self.reviewer,
            "provider": self.provider, "provenance": self.provenance,
            "task_contract_sha256": self.task_contract_sha256,
            "source_fingerprint": self.source_fingerprint, "test_fingerprint": self.test_fingerprint,
            "evidence_fingerprint": self.evidence_fingerprint, "verdict": self.verdict,
            "findings": [_json_plain(finding) for finding in self.findings],
            "reviewed_at": self.reviewed_at, "assertion_sha256": self.assertion_sha256,
        }
