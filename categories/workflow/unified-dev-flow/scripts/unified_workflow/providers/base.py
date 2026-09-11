"""Provider protocol and shared errors for local workflow observations."""
from __future__ import annotations

from typing import Protocol

from ..model import WorkspaceRevision
from ..store import ObserveRequest, VerificationResult


class ProviderError(RuntimeError):
    """A stable, caller-visible Provider failure with a machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class Provider(Protocol):
    """Observe the workspace and run only registered verification commands."""

    name: str
    version: str

    def observe_workspace(self, request: ObserveRequest) -> WorkspaceRevision:
        """Return an immutable observation for the request's workspace scope."""

    def run_verification(self, command_id: str) -> VerificationResult:
        """Run a registered command ID and return its complete stream metadata."""


__all__ = ("ObserveRequest", "Provider", "ProviderError", "VerificationResult")
