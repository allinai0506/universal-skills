"""Deterministic FIFO Provider fixtures for tests and offline demonstrations."""
from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from ..model import WorkspaceRevision
from .base import ObserveRequest, ProviderError, VerificationResult


class MockProvider:
    """Consume supplied observations and results in FIFO order without executing code."""

    name = "mock"
    version = "1"

    def __init__(self, observations: Iterable[WorkspaceRevision | BaseException],
                 results: Iterable[VerificationResult | BaseException]) -> None:
        self._observations = deque(observations)
        self._results = deque(results)

    @staticmethod
    def _next(values: deque, exhausted: str):
        if not values:
            raise ProviderError(exhausted, "No fixture remains")
        value = values.popleft()
        if isinstance(value, BaseException):
            raise value
        return value

    def observe_workspace(self, request: ObserveRequest) -> WorkspaceRevision:
        value = self._next(self._observations, "MOCK_OBSERVATIONS_EXHAUSTED")
        if not isinstance(value, WorkspaceRevision):
            raise ProviderError("INVALID_MOCK_OBSERVATION", "Fixture must be a WorkspaceRevision")
        return value

    def run_verification(self, command_id: str) -> VerificationResult:
        value = self._next(self._results, "MOCK_RESULTS_EXHAUSTED")
        if not isinstance(value, VerificationResult):
            raise ProviderError("INVALID_MOCK_RESULT", "Fixture must be a VerificationResult")
        return value
