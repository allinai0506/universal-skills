"""A trusted, caller-authority local Provider; it is explicitly not a sandbox."""
from __future__ import annotations

from datetime import datetime, timezone
from fnmatch import fnmatchcase
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
import selectors
import signal
import subprocess
import time
from typing import Mapping

from ..model import TaskContract, WorkspaceRevision
from .base import ObserveRequest, ProviderError, VerificationResult


_EXCLUDED_ROOTS = {".git", ".unified-dev-flow"}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class TrustedLocalVerifier:
    """Run caller-authorized local commands with caller-equivalent authority, not a sandbox.

    The supplied contract is the authorization boundary.  This provider does not
    isolate processes, files, network access, or operating-system credentials.
    """

    name = "trusted-local"
    version = "1"

    def __init__(self, project_root: Path, task_contract: TaskContract,
                 environment: Mapping[str, str] | None = None) -> None:
        try:
            self.project_root = Path(project_root).resolve(strict=True)
        except OSError as exc:
            raise ProviderError("INVALID_PROJECT_ROOT", "project_root cannot be resolved") from exc
        if not self.project_root.is_dir():
            raise ProviderError("INVALID_PROJECT_ROOT", "project_root must be a directory")
        self.task_contract = task_contract
        self._commands = {item.command_id: item for item in task_contract.verification_commands}
        self._environment = dict(environment or {})
        if any(not isinstance(key, str) or not key or "=" in key or "\x00" in key
               or not isinstance(value, str) or "\x00" in value
               for key, value in self._environment.items()):
            raise ProviderError("INVALID_ENVIRONMENT", "environment must contain text key/value pairs")

    def observe_workspace(self, request: ObserveRequest) -> WorkspaceRevision:
        """Hash requested real files only; control state never alters business revision."""
        digest = sha256()
        manifest: dict[str, str] = {}
        for relative, path in self._relevant_files(request.task_contract.verification_inputs):
            digest.update(relative.encode("utf-8", "surrogateescape"))
            digest.update(b"\0")
            file_digest = sha256()
            with path.open("rb") as stream:
                while block := stream.read(1024 * 1024):
                    digest.update(block)
                    file_digest.update(block)
            digest.update(b"\0")
            manifest[relative] = "sha256:" + file_digest.hexdigest()
        fingerprint = "sha256:" + digest.hexdigest()
        origin_manifest = request.scope_origin.file_manifest
        if request.scope_origin.provider == self.name and origin_manifest:
            changed_paths = tuple(sorted(path for path in set(manifest) | set(origin_manifest)
                                         if manifest.get(path) != origin_manifest.get(path)))
        else:
            # A foreign or legacy local origin cannot support task attribution.
            # Report every relevant path rather than treating Git's HEAD as its origin.
            changed_paths = tuple(manifest)
        return WorkspaceRevision.from_dict({
            "schema_version": 1,
            "provider": self.name,
            "revision_id": "workspace-" + digest.hexdigest(),
            "verification_input_fingerprint": fingerprint,
            "changed_paths": list(changed_paths),
            "observed_at": _timestamp(),
            "file_manifest": manifest,
        })

    def run_verification(self, command_id: str) -> VerificationResult:
        """Run exactly one contract command with bounded retained output."""
        command = self._commands.get(command_id)
        if command is None:
            raise ProviderError("COMMAND_NOT_REGISTERED", "command_id is not in the task contract")
        cwd = self._command_cwd(command.cwd)
        started_at = _timestamp()
        environment = {"PATH": os.defpath, "LANG": "C", "LC_ALL": "C"}
        environment.update(self._environment)
        try:
            process = subprocess.Popen(command.argv, shell=False, cwd=cwd, env=environment,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True)
        except OSError as exc:
            raise ProviderError("COMMAND_START_FAILED", "registered command could not be started") from exc

        stdout, stderr, timed_out = self._collect_output(process, command.timeout_seconds,
                                                          command.max_output_bytes)
        ended_at = _timestamp()
        return VerificationResult(started_at=started_at, ended_at=ended_at,
            exit_code=None if timed_out else process.returncode, timed_out=timed_out,
            output_truncated=stdout[1] or stderr[1], stdout=stdout[0], stderr=stderr[0],
            stdout_bytes=stdout[2], stderr_bytes=stderr[2], stdout_sha256=stdout[3],
            stderr_sha256=stderr[3])

    def _command_cwd(self, relative: str) -> Path:
        try:
            candidate = (self.project_root / relative).resolve(strict=True)
            candidate.relative_to(self.project_root)
        except (OSError, ValueError):
            raise ProviderError("CWD_ESCAPE", "registered command cwd resolves outside project_root")
        if not candidate.is_dir():
            raise ProviderError("CWD_INVALID", "registered command cwd is not a directory")
        return candidate

    def _relevant_files(self, patterns: tuple[str, ...]):
        files: list[tuple[str, Path]] = []
        for current, directory_names, file_names in os.walk(self.project_root, followlinks=False):
            current_path = Path(current)
            directory_names[:] = sorted(name for name in directory_names
                                        if name not in _EXCLUDED_ROOTS)
            for name in directory_names:
                path = current_path / name
                if path.is_symlink():
                    self._check_symlink(path)
            for name in sorted(file_names):
                path = current_path / name
                relative = path.relative_to(self.project_root).as_posix()
                if PurePosixPath(relative).parts[0] in _EXCLUDED_ROOTS:
                    continue
                if path.is_symlink():
                    self._check_symlink(path)
                    continue
                if not path.is_file():
                    continue
                if self._matches(relative, patterns):
                    files.append((relative, path))
        return sorted(files)

    def _check_symlink(self, path: Path) -> None:
        try:
            path.resolve(strict=True).relative_to(self.project_root)
        except (OSError, ValueError):
            raise ProviderError("WORKSPACE_ESCAPE", "workspace symlink resolves outside project_root")

    @staticmethod
    def _matches(relative: str, patterns: tuple[str, ...]) -> bool:
        path = PurePosixPath(relative)
        for pattern in patterns:
            if pattern in {"**", "**/*"} or fnmatchcase(relative, pattern) or path.match(pattern):
                return True
            prefix = pattern[:-3].rstrip("/") + "/"
            if pattern.endswith("/**") and relative.startswith(prefix):
                return True
        return False

    @staticmethod
    def _collect_output(process: subprocess.Popen, timeout_seconds: int, limit: int):
        retained = {"stdout": bytearray(), "stderr": bytearray()}
        counts = {"stdout": 0, "stderr": 0}
        hashes = {"stdout": sha256(), "stderr": sha256()}
        selector = selectors.DefaultSelector()
        assert process.stdout is not None and process.stderr is not None
        for label, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        deadline = time.monotonic() + timeout_seconds
        timed_out = False
        cleanup_deadline: float | None = None
        try:
            while selector.get_map() or process.poll() is None:
                now = time.monotonic()
                if not timed_out and now >= deadline:
                    timed_out = True
                    cleanup_deadline = now + 1
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if timed_out and cleanup_deadline is not None and now >= cleanup_deadline:
                    for key in list(selector.get_map().values()):
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                    break
                until = cleanup_deadline if timed_out else deadline
                wait = max(0, min(.05, until - now))
                for key, _ in selector.select(wait):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        continue
                    label = key.data
                    counts[label] += len(data)
                    hashes[label].update(data)
                    room = limit - len(retained[label])
                    if room > 0:
                        retained[label].extend(data[:room])
            if process.poll() is None:
                process.wait(timeout=1)
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=1)
            selector.close()
        streams = []
        for label in ("stdout", "stderr"):
            data = bytes(retained[label])
            streams.append((data, counts[label] > len(data), counts[label], hashes[label].hexdigest()))
        return streams[0], streams[1], timed_out
