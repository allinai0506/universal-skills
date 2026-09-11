"""Unix durable event store; workflow decisions remain in the pure Gate.

Providers consume ObserveRequest and registered command IDs, returning the
immutable VerificationResult below. No Provider implementation is required here.
"""
from __future__ import annotations

from contextlib import contextmanager, ExitStack
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
from uuid import uuid4

from .commands import Allowed, Command, Decision, Denied
from .events import DomainEvent, EventBatch, IntegrityError, ZERO_HASH
from .gate_kernel import decide
from .model import (EvidenceRecord, TaskContract, ValidationError, WorkspaceRevision,
                    canonical_json, canonical_sha256, validate_id, _json_plain)
from .reducer import RunState, initial_state, replay


@dataclass(frozen=True)
class BlobReference:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class ObserveRequest:
    task_contract: TaskContract
    scope_origin: WorkspaceRevision


@dataclass(frozen=True)
class VerificationResult:
    started_at: str
    ended_at: str
    exit_code: int | None
    timed_out: bool
    output_truncated: bool
    stdout: bytes
    stderr: bytes
    stdout_bytes: int
    stderr_bytes: int
    stdout_sha256: str
    stderr_sha256: str

    def __post_init__(self):
        for field in ("started_at", "ended_at"):
            if not isinstance(getattr(self, field), str) or not getattr(self, field):
                raise ValidationError("INVALID_PROVIDER_RESULT", f"{field} must be nonempty text")
        if self.exit_code is not None and type(self.exit_code) is not int:
            raise ValidationError("INVALID_PROVIDER_RESULT", "exit_code must be an integer or null")
        if type(self.timed_out) is not bool or type(self.output_truncated) is not bool:
            raise ValidationError("INVALID_PROVIDER_RESULT", "execution flags must be booleans")
        for stream in ("stdout", "stderr"):
            data = getattr(self, stream)
            count = getattr(self, stream + "_bytes")
            digest = getattr(self, stream + "_sha256")
            if not isinstance(data, bytes) or type(count) is not int or count < len(data):
                raise ValidationError("INVALID_PROVIDER_RESULT", "invalid stream bytes/count")
            if not isinstance(digest, str) or not re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", digest):
                raise ValidationError("INVALID_PROVIDER_RESULT", "invalid stream digest")
            if count == len(data) and digest.removeprefix("sha256:") != sha256(data).hexdigest():
                raise ValidationError("INVALID_PROVIDER_RESULT", "stream digest does not match")
            if count != len(data) and not self.output_truncated:
                raise ValidationError("INVALID_PROVIDER_RESULT", "missing truncation flag")


@dataclass(frozen=True)
class CommandResult:
    outcome: Allowed | Denied
    state: RunState | None
    diagnostics: tuple[str, ...] = ()
    status: str = "success"


class LockBusy(IntegrityError):
    def __init__(self):
        super().__init__("LOCK_BUSY", "Another operation holds the run lock")


def _denied(code, action):
    return Denied(code, (action,))


class RunStore:
    """Replay events.jsonl under a flock; never maintain a state snapshot.

All control components are opened relative to verified directory descriptors
with O_NOFOLLOW. Busy commands have state=None because no locked read occurred.
The sequence property describes the last successfully read/committed head.
"""

    def __init__(self, project_root: Path, work_id: str):
        self.work_id = validate_id(work_id, "work_id")
        self.project_root = Path(project_root).resolve(strict=True)
        if not self.project_root.is_dir():
            raise ValidationError("INVALID_PATH", "project_root must be a directory")
        self.run_dir = self.project_root / ".unified-dev-flow" / "runs" / work_id
        self.events_path = self.run_dir / "events.jsonl"
        self.lock_path = self.run_dir / "run.lock"
        self.sequence = 0
        self.diagnostics: tuple[str, ...] = ()

    @staticmethod
    def _directory(parent_fd, name):
        created = False
        try:
            os.mkdir(name, mode=0o700, dir_fd=parent_fd)
            created = True
        except FileExistsError:
            pass
        try:
            fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
        except OSError as exc:
            raise ValidationError("UNSAFE_CONTROL_PATH", f"Invalid control directory {name}") from exc
        try:
            os.fchmod(fd, 0o700)
            if created:
                os.fsync(fd)
                os.fsync(parent_fd)
            return fd
        except BaseException:
            os.close(fd)
            raise

    @contextmanager
    def _layout(self):
        with ExitStack() as stack:
            root_fd = os.open(self.project_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            stack.callback(os.close, root_fd)
            current = root_fd
            for name in (".unified-dev-flow", "runs", self.work_id):
                current = self._directory(current, name)
                stack.callback(os.close, current)
            blobs = self._directory(current, "blobs")
            stack.callback(os.close, blobs)
            yield current, blobs

    @staticmethod
    def _file(directory_fd, name, flags):
        try:
            fd = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=directory_fd)
        except OSError as exc:
            raise ValidationError("UNSAFE_CONTROL_PATH", f"Cannot open control file {name}") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValidationError("UNSAFE_CONTROL_PATH", f"Control file {name} must be a private regular file")
            os.fchmod(fd, 0o600)
            if flags & os.O_CREAT:
                os.fsync(directory_fd)
            return fd
        except BaseException:
            os.close(fd)
            raise

    @contextmanager
    def _locked(self, exclusive=True):
        with self._layout() as (run_fd, blobs_fd):
            lock = self._file(run_fd, "run.lock", os.O_RDWR | os.O_CREAT)
            try:
                try:
                    fcntl.flock(lock, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise LockBusy() from exc
                os.close(self._file(run_fd, "events.jsonl", os.O_RDWR | os.O_CREAT))
                yield run_fd, blobs_fd
            finally:
                os.close(lock)

    def _read(self, run_fd, blobs_fd):
        fd = self._file(run_fd, "events.jsonl", os.O_RDONLY)
        with os.fdopen(fd, "rb") as stream:
            data = stream.read()
        if data and not data.endswith(b"\n"):
            raise IntegrityError("EVENT_JSON_CORRUPT", "Event log has an unterminated final record")
        batches = []
        try:
            for line in data.splitlines():
                raw = json.loads(line.decode("utf-8"), object_pairs_hook=self._unique_object)
                batch = EventBatch.from_dict(raw)
                if batch.work_id != self.work_id:
                    raise IntegrityError("EVENT_WORK_ID_MISMATCH", "Batch belongs to another run")
                batches.append(batch)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise IntegrityError("EVENT_JSON_CORRUPT", "Cannot decode event record") from exc
        state = replay(batches)
        if state.work_id not in (None, self.work_id):
            raise IntegrityError("EVENT_WORK_ID_MISMATCH", "Run belongs to another work ID")
        self.sequence = len(batches)
        self.diagnostics = self._blob_diagnostics(state, blobs_fd)
        return batches, state

    @staticmethod
    def _unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise IntegrityError("EVENT_JSON_CORRUPT", "Duplicate JSON key")
            result[key] = value
        return result

    def load(self) -> RunState:
        with self._locked(exclusive=False) as (run_fd, blobs_fd):
            return self._read(run_fd, blobs_fd)[1]

    def _blob_diagnostics(self, state, blobs_fd):
        warnings = set()
        for event in state.events:
            evidence = event.payload.get("evidence")
            if evidence is None:
                continue
            for stream in ("stdout", "stderr"):
                ref = evidence.get(stream + "_blob_ref")
                if ref is None:
                    continue
                if not isinstance(ref, str) or not re.fullmatch(r"blobs/[0-9a-f]{64}", ref):
                    warnings.add("INVALID_DIAGNOSTIC_BLOB_REFERENCE")
                    continue
                try:
                    fd = os.open(ref[6:], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=blobs_fd)
                    with os.fdopen(fd, "rb") as blob:
                        if not stat.S_ISREG(os.fstat(blob.fileno()).st_mode):
                            warnings.add("INVALID_DIAGNOSTIC_BLOB_REFERENCE")
                            continue
                        digest = sha256()
                        for chunk in iter(lambda: blob.read(65536), b""):
                            digest.update(chunk)
                        if digest.hexdigest() != ref[6:]:
                            warnings.add("DIAGNOSTIC_BLOB_DIGEST_MISMATCH")
                except FileNotFoundError:
                    warnings.add("MISSING_DIAGNOSTIC_BLOB")
                except OSError:
                    warnings.add("INVALID_DIAGNOSTIC_BLOB_REFERENCE")
        return tuple(sorted(warnings))

    def _publish_blob(self, data, blobs_fd):
        if not isinstance(data, bytes):
            raise ValidationError("INVALID_TYPE", "Blob must be bytes")
        digest = sha256(data).hexdigest()
        name = uuid4().hex + ".tmp"
        fd = self._file(blobs_fd, name, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, digest, src_dir_fd=blobs_fd, dst_dir_fd=blobs_fd)
            os.fsync(blobs_fd)
        finally:
            try:
                os.unlink(name, dir_fd=blobs_fd)
            except FileNotFoundError:
                pass
        return BlobReference("blobs/" + digest, "sha256:" + digest, len(data))

    def publish_blob(self, data: bytes) -> BlobReference:
        with self._locked() as (_, blobs_fd):
            return self._publish_blob(data, blobs_fd)

    def _result(self, state, outcome, status=None):
        return CommandResult(outcome, state, self.diagnostics,
                             status or ("success" if isinstance(outcome, Allowed) else "denied"))

    def _prior(self, run_fd, state, command, fingerprint):
        if command.work_id != self.work_id:
            return self._result(state, _denied("INVALID_CONTRACT", "Address this store's work ID."))
        existing = state.requests.get(command.request_id)
        if existing is not None:
            if existing.request_sha256 != fingerprint:
                return self._result(state, _denied("IDEMPOTENCY_CONFLICT", "Use a new request ID for a different command."))
            if existing.status == "in_doubt":
                return self._result(state, _denied("REQUEST_IN_DOUBT", "Inspect the prior attempt and explicitly resolve it."))
            summary = _json_plain(existing.result_summary)
            outcome = Decision.from_dict({"events": [], "outcome": summary["outcome"]}).outcome
            # A prior append may be readable even if its fsync raised. Reestablish
            # durability under the writer lock before acknowledging that outcome.
            fd = self._file(run_fd, "events.jsonl", os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(run_fd)
            return self._result(state, outcome, existing.outcome)
        if command.expected_sequence != self.sequence:
            return self._result(state, _denied("EXPECTED_SEQUENCE_MISMATCH", "Reload the run and use its current sequence."))
        return None

    @staticmethod
    def _reservation(command, fingerprint, sequence):
        return DomainEvent("REQUEST_RESERVED", dict(request_id=command.request_id,
            request_sha256=fingerprint, command_type=command.command_type, reservation_sequence=sequence))

    def _append(self, run_fd, blobs_fd, batches, command, fingerprint, events, batch_id=None):
        batch = EventBatch.create(sequence=len(batches) + 1, batch_id=batch_id or uuid4().hex,
            request_id=command.request_id, request_sha256=fingerprint, work_id=self.work_id,
            occurred_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            actor=command.actor, previous_hash=batches[-1].batch_hash if batches else ZERO_HASH,
            events=events)
        state = replay([*batches, batch])
        encoded = (canonical_json(batch.to_dict()) + "\n").encode("utf-8")
        fd = self._file(run_fd, "events.jsonl", os.O_WRONLY | os.O_APPEND)
        with os.fdopen(fd, "ab") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(run_fd)
        batches.append(batch)
        self.sequence = batch.sequence
        self.diagnostics = self._blob_diagnostics(state, blobs_fd)
        return state

    def _finish(self, run_fd, blobs_fd, batches, command, fingerprint, decision,
                *, reserve=False, status=None, note=None):
        status = status or ("success" if isinstance(decision.outcome, Allowed) else "denied")
        batch_id = uuid4().hex
        events = list(decision.events)
        if reserve:
            events.insert(0, self._reservation(command, fingerprint, len(batches) + 1))
        summary = {"outcome": decision.to_dict()["outcome"]}
        if note is not None:
            summary["note"] = note
        events.append(DomainEvent("REQUEST_RESOLVED", dict(request_id=command.request_id,
            outcome=status, reason_code=getattr(decision.outcome, "reason_code", None),
            result_summary=summary, event_ids=[f"{batch_id}.{i + int(reserve)}"
                                             for i, _ in enumerate(decision.events)])))
        state = self._append(run_fd, blobs_fd, batches, command, fingerprint, events, batch_id)
        return self._result(state, decision.outcome, status)

    def _run_is_absent(self):
        with ExitStack() as stack:
            current = os.open(self.project_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            stack.callback(os.close, current)
            for name in (".unified-dev-flow", "runs", self.work_id):
                try:
                    current = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
                except FileNotFoundError:
                    return True
                except OSError as exc:
                    raise ValidationError("UNSAFE_CONTROL_PATH", f"Invalid control directory {name}") from exc
                stack.callback(os.close, current)
            return False

    def execute(self, command, facts=None) -> CommandResult:
        command = Command.from_dict(command.to_dict())
        if command.command_type == "INIT_RUN" and self._run_is_absent():
            preflight = decide(initial_state(), command, facts)
            # Recheck after preflight: a concurrent creator must enter the normal
            # locked replay path. This final absent lookup linearizes a no-write denial.
            if isinstance(preflight.outcome, Denied) and self._run_is_absent():
                return self._result(initial_state(), preflight.outcome)
        fingerprint = canonical_sha256(command.to_dict())
        try:
            with self._locked() as (run_fd, blobs_fd):
                batches, state = self._read(run_fd, blobs_fd)
                if command.command_type == "RECORD_VERIFICATION":
                    return self._result(state, _denied("INVALID_CONTRACT",
                        "Use execute_verification with a registered command ID and Provider."))
                prior = self._prior(run_fd, state, command, fingerprint)
                if prior is not None:
                    return prior
                decision = decide(state, command, facts)
                return self._finish(run_fd, blobs_fd, batches, command, fingerprint, decision, reserve=True)
        except LockBusy:
            return CommandResult(_denied("LOCK_BUSY", "Retry when the writer releases the lock."), None, (), "denied")

    def execute_verification(self, command, provider) -> CommandResult:
        command = Command.from_dict(command.to_dict())
        fingerprint = canonical_sha256(command.to_dict())
        try:
            with self._locked() as (run_fd, blobs_fd):
                batches, state = self._read(run_fd, blobs_fd)
                prior = self._prior(run_fd, state, command, fingerprint)
                if prior is not None:
                    return prior
                task = state.tasks.get(command.task_id)
                registered = None if task is None else next((item for item in task.contract.verification_commands
                    if item.command_id == command.payload.get("command_id")), None)
                if (command.command_type != "RECORD_VERIFICATION" or set(command.payload) != {"command_id"}
                        or registered is None):
                    rejection = Decision((), _denied("INVALID_CONTRACT", "Select a registered verification command ID."))
                    return self._finish(run_fd, blobs_fd, batches, command, fingerprint, rejection, reserve=True)
                if state.status != "active" or task.status != "running" or task.scope_origin is None:
                    rejection = decide(state, replace(command, payload={}), None)
                    return self._finish(run_fd, blobs_fd, batches, command, fingerprint, rejection, reserve=True)
                state = self._append(run_fd, blobs_fd, batches, command, fingerprint,
                    [self._reservation(command, fingerprint, len(batches) + 1)])
                request = ObserveRequest(task.contract, WorkspaceRevision.from_dict(_json_plain(task.scope_origin)))
                try:
                    pre = WorkspaceRevision.from_dict(provider.observe_workspace(request).to_dict())
                    result = provider.run_verification(registered.command_id)
                    if not isinstance(result, VerificationResult):
                        raise ValidationError("INVALID_PROVIDER_RESULT", "Provider must return VerificationResult")
                    result = replace(result)
                    if len(result.stdout) > registered.max_output_bytes or len(result.stderr) > registered.max_output_bytes:
                        raise ValidationError("INVALID_PROVIDER_RESULT", "Provider exceeded the retained output limit")
                    post = WorkspaceRevision.from_dict(provider.observe_workspace(request).to_dict())
                except Exception:
                    return self._finish(run_fd, blobs_fd, batches, command, fingerprint,
                        Decision((), _denied("PROVIDER_FAILURE", "Inspect provider failure and issue a new request.")),
                        status="provider_failure")
                stdout = self._publish_blob(result.stdout, blobs_fd)
                stderr = self._publish_blob(result.stderr, blobs_fd)
                try:
                    commit = WorkspaceRevision.from_dict(provider.observe_workspace(request).to_dict())
                    raw = dict(schema_version=1, task_id=task.task_id, task_revision=task.task_revision,
                        task_contract_sha256=canonical_sha256(task.contract.to_dict()),
                        command_id=registered.command_id, command_sha256=canonical_sha256(registered.to_dict()),
                        provider=provider.name, provider_version=provider.version,
                        pre_command_revision=pre.to_dict(), post_command_revision=post.to_dict(),
                        commit_revision=commit.to_dict(), started_at=result.started_at, ended_at=result.ended_at,
                        exit_code=result.exit_code, timed_out=result.timed_out, output_truncated=result.output_truncated,
                        stdout_bytes=result.stdout_bytes, stdout_sha256="sha256:" + result.stdout_sha256.removeprefix("sha256:"),
                        stdout_blob_ref=stdout.path, stderr_bytes=result.stderr_bytes,
                        stderr_sha256="sha256:" + result.stderr_sha256.removeprefix("sha256:"), stderr_blob_ref=stderr.path,
                        scope_diff=sorted(set(pre.changed_paths + post.changed_paths + commit.changed_paths)),
                        verification_input_fingerprint=pre.verification_input_fingerprint)
                    evidence = EvidenceRecord.from_dict({**raw, "evidence_sha256": canonical_sha256(raw)})
                except Exception:
                    return self._finish(run_fd, blobs_fd, batches, command, fingerprint,
                        Decision((), _denied("PROVIDER_FAILURE", "Inspect provider failure and issue a new request.")),
                        status="provider_failure")
                decision = decide(state, replace(command, payload={"evidence": evidence.to_dict()}), commit)
                return self._finish(run_fd, blobs_fd, batches, command, fingerprint, decision)
        except LockBusy:
            return CommandResult(_denied("LOCK_BUSY", "Retry when the writer releases the lock."), None, (), "denied")

    def resolve_request(self, request_id, outcome, actor, note, expected_sequence: int | None = None) -> CommandResult:
        validate_id(request_id, "request_id")
        if outcome not in ("success", "denied", "provider_failure", "abandoned"):
            raise ValidationError("INVALID_VALUE", "Unsupported resolution outcome")
        if not isinstance(note, str) or not note.strip():
            raise ValidationError("INVALID_VALUE", "Audited resolution requires a note")
        if expected_sequence is not None and (type(expected_sequence) is not int or expected_sequence < 0):
            raise ValidationError("INVALID_VALUE", "expected_sequence must be a nonnegative integer")
        try:
            with self._locked() as (run_fd, blobs_fd):
                batches, state = self._read(run_fd, blobs_fd)
                if expected_sequence is not None and expected_sequence != self.sequence:
                    return self._result(state, _denied("EXPECTED_SEQUENCE_MISMATCH", "Reload the run and use its current sequence."))
                existing = state.requests.get(request_id)
                if existing is None or existing.status != "in_doubt":
                    return self._result(state, _denied("INVALID_TRANSITION", "Resolve an existing in-doubt request."))
                cmd = Command.from_dict(dict(schema_version=1, request_id=request_id,
                    command_type=existing.command_type, work_id=self.work_id, task_id=None,
                    actor=_json_plain(actor), expected_sequence=self.sequence, payload={}))
                resolved = Allowed({"note": note}) if outcome == "success" else _denied(
                    "REQUEST_" + outcome.upper(), "Use a new request ID for any subsequent attempt.")
                return self._finish(run_fd, blobs_fd, batches, cmd, existing.request_sha256,
                    Decision((), resolved), status=outcome, note=note)
        except LockBusy:
            return CommandResult(_denied("LOCK_BUSY", "Retry when the writer releases the lock."), None, (), "denied")
