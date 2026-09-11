"""A trusted, caller-authority local Provider; it is explicitly not a sandbox."""
from __future__ import annotations

from datetime import datetime, timezone
from fnmatch import fnmatchcase
from hashlib import sha256
import os
from pathlib import Path, PurePosixPath
import selectors
import signal
import stat
import subprocess
import time
from typing import Mapping

from ..model import TaskContract, WorkspaceRevision, canonical_sha256
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
        """Observe the whole project for scope, and selected inputs for freshness."""
        manifest, links, directories = self._workspace_manifest()
        selected = {path for path in manifest
                    if self._matches(path, request.task_contract.verification_inputs)}
        selected_directories = {path for path in directories
                                if self._matches(path, request.task_contract.verification_inputs)}
        selected.update(path for path in manifest
                        if any(path.startswith(directory + "/") for directory in selected_directories))
        # A selected child must also bind every containing link's identity.
        selected.update(link for link in links
                        if any(path.startswith(link + "/") for path in selected))
        fingerprint = canonical_sha256({path: manifest[path] for path in sorted(selected)})
        origin_manifest = request.scope_origin.file_manifest
        if request.scope_origin.provider != self.name or origin_manifest is None:
            raise ProviderError("SCOPE_ORIGIN_MANIFEST_UNAVAILABLE",
                                "scope origin cannot support exact local attribution")
        changed_paths = tuple(sorted(path for path in set(manifest) | set(origin_manifest)
                                     if manifest.get(path) != origin_manifest.get(path)))
        return WorkspaceRevision.from_dict({
            "schema_version": 1,
            "provider": self.name,
            "revision_id": "workspace-" + canonical_sha256(manifest).removeprefix("sha256:"),
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

    def _workspace_manifest(self):
        manifest: dict[str, str] = {}
        links: set[str] = set()
        directories: set[str] = set()

        def visit(path: Path, relative: str, ancestors: frozenset[Path]):
            linked = path.is_symlink()
            resolved = self._check_symlink(path) if linked else path.resolve(strict=True)
            if path.is_dir():
                if resolved in ancestors:
                    raise ProviderError("WORKSPACE_CYCLE", "workspace directory links form a cycle")
                for child in sorted(path.iterdir()):
                    visit(child, relative + "/" + child.name, ancestors | {resolved})
                directories.add(relative)
                content = None
            elif path.is_file():
                digest = sha256()
                with path.open("rb") as stream:
                    while block := stream.read(1024 * 1024):
                        digest.update(block)
                    mode = stat.S_IMODE(os.fstat(stream.fileno()).st_mode)
                content = canonical_sha256({"content_sha256": "sha256:" + digest.hexdigest(), "mode": mode})
                manifest[relative] = content
            else:
                raise ProviderError("UNSUPPORTED_WORKSPACE_ENTRY", "workspace entry is not a regular file or directory")
            if linked:
                links.add(relative)
                manifest[relative] = canonical_sha256({"link_target": os.readlink(path),
                    "resolved_path": resolved.relative_to(self.project_root).as_posix(),
                    "content_sha256": content})

        for child in sorted(self.project_root.iterdir()):
            if child.name not in _EXCLUDED_ROOTS:
                visit(child, child.name, frozenset({self.project_root}))
        return dict(sorted(manifest.items())), links, directories

    def _check_symlink(self, path: Path) -> Path:
        try:
            resolved = path.resolve(strict=True)
            relative = resolved.relative_to(self.project_root)
        except (OSError, ValueError, RuntimeError):
            raise ProviderError("WORKSPACE_ESCAPE", "workspace symlink resolves outside project_root")
        if relative.parts and relative.parts[0] in _EXCLUDED_ROOTS:
            raise ProviderError("WORKSPACE_CONTROL_PATH", "workspace symlink resolves into control state")
        return resolved

    @staticmethod
    def _matches(relative: str, patterns: tuple[str, ...]) -> bool:
        def matches(parts, pattern):
            if not pattern:
                return not parts
            if pattern[0] == "**":
                return matches(parts, pattern[1:]) or bool(parts) and matches(parts[1:], pattern)
            return bool(parts) and fnmatchcase(parts[0], pattern[0]) and matches(parts[1:], pattern[1:])

        return any(matches(PurePosixPath(relative).parts, PurePosixPath(pattern).parts) for pattern in patterns)

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
