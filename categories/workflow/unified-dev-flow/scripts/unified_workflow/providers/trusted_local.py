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
        for relative, path in self._relevant_files(request.task_contract.verification_inputs):
            digest.update(relative.encode("utf-8", "surrogateescape"))
            digest.update(b"\0")
            with path.open("rb") as stream:
                while block := stream.read(1024 * 1024):
                    digest.update(block)
            digest.update(b"\0")
        fingerprint = "sha256:" + digest.hexdigest()
        return WorkspaceRevision.from_dict({
            "schema_version": 1,
            "provider": self.name,
            "revision_id": "workspace-" + digest.hexdigest(),
            "verification_input_fingerprint": fingerprint,
            "changed_paths": list(self._git_changed_paths()),
            "observed_at": _timestamp(),
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
                if path.is_symlink():
                    self._check_symlink(path)
                    continue
                if not path.is_file():
                    continue
                if self._matches(relative, patterns):
                    files.append((relative, path))
        return files

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

    def _git_changed_paths(self) -> tuple[str, ...]:
        try:
            completed = subprocess.run(["git", "-C", str(self.project_root), "status",
                "--porcelain=v1", "-z", "--untracked-files=all"], stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, timeout=5,
                env={"PATH": os.defpath, "LANG": "C", "LC_ALL": "C"})
        except (OSError, subprocess.TimeoutExpired):
            return ()
        if completed.returncode:
            return ()
        entries = completed.stdout.split(b"\0")
        paths: set[str] = set()
        index = 0
        while index < len(entries):
            entry = entries[index]
            index += 1
            if not entry:
                continue
            status, raw_path = entry[:2], entry[3:]
            if b"\0" in raw_path:
                continue
            if b"R" in status or b"C" in status:
                index += 1
            path = raw_path.decode("utf-8", "surrogateescape")
            pure = PurePosixPath(path)
            if (not path or pure.is_absolute() or ".." in pure.parts or "\\" in path
                    or pure.parts[0] in _EXCLUDED_ROOTS):
                continue
            paths.add(path)
        return tuple(sorted(paths))

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
        try:
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if not timed_out and remaining <= 0 and process.poll() is None:
                    timed_out = True
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                wait = .05 if timed_out else max(0, min(.05, remaining))
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
            process.wait()
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            selector.close()
        streams = []
        for label in ("stdout", "stderr"):
            data = bytes(retained[label])
            streams.append((data, counts[label] > len(data), counts[label], hashes[label].hexdigest()))
        return streams[0], streams[1], timed_out
