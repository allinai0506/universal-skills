"""Pure immutable reducer for Unified Workflow domain events."""
from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any, Mapping

from .events import DomainEvent, EventBatch, IntegrityError, ZERO_HASH, verify_batch
from .model import RouteContract, TaskContract, ValidationError, canonical_sha256, validate_id


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list) or isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


@dataclass(frozen=True)
class RequestState:
    request_id: str
    request_sha256: str
    command_type: str
    reservation_sequence: int | None
    status: str
    expected_sequence: int
    outcome: str | None = None
    reason_code: str | None = None
    result_summary: Mapping[str, Any] | None = None
    event_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskState:
    task_id: str
    contract: TaskContract
    status: str = "draft"
    task_revision: int = 1
    scope_origin: Any = None
    review_round: int = 0
    current_input_fingerprint: str | None = None
    current_fresh_verdict_fingerprint: str | None = None
    accepted_task_revision: int | None = None
    accepted_input_fingerprint: str | None = None
    accepted_verdict_fingerprint: str | None = None
    currently_satisfied: bool = False
    reports: tuple[Mapping[str, Any], ...] = ()
    verifications: tuple[Mapping[str, Any], ...] = ()
    reviews: tuple[Mapping[str, Any], ...] = ()
    history: tuple[DomainEvent, ...] = ()


@dataclass(frozen=True)
class RunState:
    schema_version: int
    status: str
    work_id: str | None
    tasks: Mapping[str, TaskState]
    requests: Mapping[str, RequestState]
    deliveries: tuple[Mapping[str, Any], ...]
    events: tuple[DomainEvent, ...]
    acceptance_set_sha256: str
    goal: str | None
    route_contract: RouteContract | None
    route_contract_sha256: str | None
    review_rounds_by_task: Mapping[str, int]
    blockers: tuple[Mapping[str, Any], ...]
    latest_sequence: int
    latest_hash: str
    created_at: str | None
    updated_at: str | None


def initial_state() -> RunState:
    return RunState(
        schema_version=1, status="new", work_id=None, tasks=MappingProxyType({}),
        requests=MappingProxyType({}), deliveries=(), events=(),
        acceptance_set_sha256=canonical_sha256([]),
        goal=None, route_contract=None, route_contract_sha256=None,
        review_rounds_by_task=MappingProxyType({}), blockers=(), latest_sequence=0,
        latest_hash=ZERO_HASH, created_at=None, updated_at=None,
    )


def _error(code: str, message: str) -> None:
    raise IntegrityError(code, message)


def _digest(value: Any, field: str) -> str:
    if (not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:")
            or any(character not in "0123456789abcdef" for character in value[7:])):
        _error("EVENT_SCHEMA_MISMATCH", f"{field} must be a sha256: digest")
    return value


def _payload(event: DomainEvent) -> Mapping[str, Any]:
    if not isinstance(event.payload, Mapping):
        _error("EVENT_SCHEMA_MISMATCH", "event payload must be an object")
    return event.payload


def _task(state: RunState, payload: Mapping[str, Any]) -> TaskState:
    task_id = validate_id(payload.get("task_id"), "task_id")
    try:
        return state.tasks[task_id]
    except KeyError:
        _error("UNKNOWN_TASK", f"task {task_id!r} does not exist")


def _replace_task(state: RunState, task: TaskState) -> RunState:
    tasks = dict(state.tasks)
    tasks[task.task_id] = task
    return replace(state, tasks=MappingProxyType(tasks))


def _clear_acceptance(task: TaskState, *, status: str | None = None,
                      reset_origin: bool = False) -> TaskState:
    return replace(
        task, status=status or task.status, scope_origin=None if reset_origin else task.scope_origin,
        current_fresh_verdict_fingerprint=None, accepted_task_revision=None,
        accepted_input_fingerprint=None, accepted_verdict_fingerprint=None,
        currently_satisfied=False,
    )


def _task_with_history(task: TaskState, event: DomainEvent) -> TaskState:
    return replace(task, history=task.history + (event,))


def _refresh_satisfaction(state: RunState) -> RunState:
    tasks = dict(state.tasks)
    satisfied: dict[str, bool] = {}
    pending = set(tasks)
    while pending:
        progressed = False
        for task_id in tuple(pending):
            task = tasks[task_id]
            if any(dependency not in tasks for dependency in task.contract.dependencies):
                value = False
            elif any(dependency in pending for dependency in task.contract.dependencies):
                continue
            else:
                value = (
                    task.status == "accepted"
                    and task.accepted_task_revision == task.task_revision
                    and task.accepted_input_fingerprint == task.current_input_fingerprint
                    and task.accepted_verdict_fingerprint == task.current_fresh_verdict_fingerprint
                    and all(satisfied[dependency] for dependency in task.contract.dependencies)
                )
            satisfied[task_id] = value
            pending.remove(task_id)
            progressed = True
        if not progressed:
            for task_id in pending:
                satisfied[task_id] = False
            break
    refreshed = {task_id: replace(task, currently_satisfied=satisfied[task_id])
                 for task_id, task in tasks.items()}
    acceptance = [
        {"task_id": task.task_id, "task_revision": task.task_revision,
         "input_fingerprint": task.accepted_input_fingerprint,
         "verdict_fingerprint": task.accepted_verdict_fingerprint}
        for task in sorted(refreshed.values(), key=lambda item: item.task_id)
        if task.contract.required and task.currently_satisfied
    ]
    blockers = []
    if state.status == "blocked":
        blockers.append(_freeze({"task_id": None, "reason_codes": ("RUN_BLOCKED",)}))
    for task in sorted(refreshed.values(), key=lambda item: item.task_id):
        reasons = set()
        for event in task.history:
            if event.event_type == "TASK_UNBLOCKED":
                reasons.clear()
            elif event.event_type in ("SCOPE_VIOLATION", "TASK_BLOCKED", "ESCALATE_TO_HUMAN"):
                reasons.add(event.event_type)
        if reasons or task.status == "blocked":
            blockers.append(_freeze({"task_id": task.task_id,
                "reason_codes": tuple(sorted(reasons or {"TASK_BLOCKED"}))}))
    return replace(state, tasks=MappingProxyType(refreshed),
                   acceptance_set_sha256=canonical_sha256(acceptance),
                   review_rounds_by_task=MappingProxyType({identifier: task.review_round
                       for identifier, task in sorted(refreshed.items())}), blockers=tuple(blockers))


def _invalidate(state: RunState, task_id: str, revision: int, event: DomainEvent) -> RunState:
    dependents: dict[str, set[str]] = {identifier: set() for identifier in state.tasks}
    for candidate in state.tasks.values():
        for dependency in candidate.contract.dependencies:
            if dependency in dependents:
                dependents[dependency].add(candidate.task_id)
    affected = {task_id}
    frontier = [task_id]
    while frontier:
        current = frontier.pop()
        for dependent in dependents[current]:
            if dependent not in affected:
                affected.add(dependent)
                frontier.append(dependent)
    tasks = dict(state.tasks)
    for identifier in affected:
        task = tasks[identifier]
        unresolved_scope = False
        for fact in task.history:
            if fact.event_type == "SCOPE_VIOLATION":
                unresolved_scope = True
            elif fact.event_type == "TASK_UNBLOCKED":
                unresolved_scope = False
        next_revision = revision if identifier == task_id else task.task_revision + 1
        reset_origin = (next_revision > task.task_revision and not unresolved_scope
                        and (identifier == task_id or task.status == "accepted"))
        task = _clear_acceptance(task, status="stale", reset_origin=reset_origin)
        task = replace(task, task_revision=next_revision)
        tasks[identifier] = _task_with_history(task, event)
    return replace(state, tasks=MappingProxyType(tasks))


def reduce_event(state: RunState, event: DomainEvent) -> RunState:
    """Apply one already-validated event without reading external state."""
    if not isinstance(event, DomainEvent):
        event = DomainEvent.from_dict(event)
    else:
        event = DomainEvent(event.event_type, event.payload)
    payload = _payload(event)
    event_type = event.event_type
    if event_type == "REQUEST_RESERVED":
        request_id = validate_id(payload.get("request_id"), "request_id")
        request_sha256 = _digest(payload.get("request_sha256"), "request_sha256")
        command_type = validate_id(payload.get("command_type"), "command_type")
        reservation_sequence = payload.get("reservation_sequence")
        if not isinstance(reservation_sequence, int) or isinstance(reservation_sequence, bool):
            _error("EVENT_SCHEMA_MISMATCH", "reservation_sequence must be an integer")
        existing = state.requests.get(request_id)
        if existing is not None:
            if (existing.request_sha256, existing.command_type, existing.reservation_sequence) != (
                    request_sha256, command_type, reservation_sequence):
                _error("REQUEST_CONFLICT", "request reservation conflicts with existing request")
            return replace(state, events=state.events + (event,))
        request = RequestState(request_id, request_sha256, command_type, reservation_sequence,
                               "in_doubt", reservation_sequence - 1)
        requests = dict(state.requests)
        requests[request_id] = request
        state = replace(state, requests=MappingProxyType(requests))
    elif event_type == "REQUEST_RESOLVED":
        request_id = validate_id(payload.get("request_id"), "request_id")
        existing = state.requests.get(request_id)
        if existing is None:
            existing = RequestState(request_id, payload["request_sha256"], payload["command_type"],
                                    None, "resolved", payload["expected_sequence"])
        elif (existing.request_sha256, existing.command_type, existing.expected_sequence) != (
                payload["request_sha256"], payload["command_type"], payload["expected_sequence"]):
            _error("REQUEST_CONFLICT", "request resolution conflicts with its original identity")
        outcome = payload.get("outcome")
        if outcome not in ("success", "denied", "provider_failure", "abandoned"):
            _error("EVENT_SCHEMA_MISMATCH", "request outcome is unsupported")
        reason_code = payload.get("reason_code")
        if reason_code is not None:
            reason_code = validate_id(reason_code, "reason_code")
        summary = _freeze(payload.get("result_summary", {}))
        if not isinstance(summary, Mapping):
            _error("EVENT_SCHEMA_MISMATCH", "result_summary must be an object")
        event_ids = payload.get("event_ids", [])
        if not isinstance(event_ids, (list, tuple)):
            _error("EVENT_SCHEMA_MISMATCH", "event_ids must be a list")
        event_ids = tuple(validate_id(item, "event_ids[]") for item in event_ids)
        resolved = replace(existing, status="resolved", outcome=outcome, reason_code=reason_code,
                           result_summary=summary, event_ids=event_ids)
        if request_id in state.requests and existing.status == "resolved":
            if existing != resolved:
                _error("REQUEST_RESOLUTION_CONFLICT", "request already has a different resolution")
            return replace(state, events=state.events + (event,))
        requests = dict(state.requests)
        requests[request_id] = resolved
        state = replace(state, requests=MappingProxyType(requests))
    elif event_type == "RUN_CREATED":
        if state.work_id is not None:
            _error("DUPLICATE_RUN", "RUN_CREATED cannot replace an existing run contract")
        route = RouteContract.from_dict(_plain(payload["route"]))
        state = replace(state, status="active", work_id=validate_id(payload.get("work_id"), "work_id"),
                        goal=payload["goal"], route_contract=route,
                        route_contract_sha256=canonical_sha256(route.to_dict()))
    elif event_type == "RUN_BLOCKED":
        state = replace(state, status="blocked")
    elif event_type == "RUN_RESUMED":
        state = replace(state, status="active")
    elif event_type == "RUN_COMPLETED":
        state = replace(state, status="completed")
    elif event_type == "RUN_CANCELLED":
        state = replace(state, status="cancelled")
    elif event_type == "TASK_ADDED":
        raw_contract = payload.get("task")
        contract = (raw_contract if isinstance(raw_contract, TaskContract)
                    else TaskContract.from_dict(_plain(raw_contract)))
        if contract.task_id in state.tasks:
            _error("DUPLICATE_TASK", f"task {contract.task_id!r} already exists")
        tasks = dict(state.tasks)
        tasks[contract.task_id] = _task_with_history(TaskState(contract.task_id, contract), event)
        state = replace(state, tasks=MappingProxyType(tasks))
    elif event_type == "TASK_INVALIDATED":
        task = _task(state, payload)
        revision = payload.get("new_task_revision")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < task.task_revision:
            _error("EVENT_SCHEMA_MISMATCH", "new_task_revision must not regress the task revision")
        state = _invalidate(state, task.task_id, revision, event)
    elif event_type == "DELIVERY_RECORDED":
        state = replace(state, deliveries=state.deliveries + (_freeze(payload),))
    else:
        task = _task(state, payload)
        if event_type == "TASK_READIED":
            task = replace(task, status="ready")
        elif event_type == "TASK_STARTED":
            origin = payload.get("scope_origin", task.scope_origin)
            if task.scope_origin is not None and origin != task.scope_origin:
                _error("EVENT_SCHEMA_MISMATCH", "scope_origin cannot replace an existing revision origin")
            task = replace(task, status="running", scope_origin=origin)
        elif event_type == "TASK_REPORTED":
            task = replace(task, reports=task.reports + (_freeze(payload),))
        elif event_type == "VERIFICATION_RECORDED":
            task = replace(task, verifications=task.verifications + (_freeze(payload),),
                           status="running" if payload.get("success") else "ready")
        elif event_type == "TASK_WAITING_REVIEW":
            task = replace(task, status="waiting_review")
        elif event_type == "REVIEW_RECORDED":
            fingerprint = _digest(payload.get("verdict_fingerprint"), "verdict_fingerprint")
            task = replace(task, reviews=task.reviews + (_freeze(payload),),
                           current_fresh_verdict_fingerprint=fingerprint)
        elif event_type == "TASK_NEEDS_FIXES":
            task = _clear_acceptance(task, status="ready")
            task = replace(task, review_round=task.review_round + 1)
            if task.review_round >= 3:
                task = replace(task, status="blocked")
                state = replace(state, status="blocked")
        elif event_type == "TASK_ACCEPTED":
            input_fingerprint = _digest(payload.get("input_fingerprint"), "input_fingerprint")
            verdict_fingerprint = _digest(payload.get("verdict_fingerprint"), "verdict_fingerprint")
            task = replace(task, status="accepted", current_input_fingerprint=input_fingerprint,
                           current_fresh_verdict_fingerprint=verdict_fingerprint,
                           accepted_task_revision=task.task_revision,
                           accepted_input_fingerprint=input_fingerprint,
                           accepted_verdict_fingerprint=verdict_fingerprint)
        elif event_type == "TASK_BLOCKED":
            task = replace(task, status="blocked", review_round=payload.get("review_round", task.review_round))
        elif event_type == "TASK_UNBLOCKED":
            task = replace(task, status="ready")
        elif event_type == "TASK_FAILED":
            task = replace(task, status="failed")
        elif event_type == "TASK_CANCELLED":
            task = replace(task, status="cancelled")
        elif event_type == "SCOPE_VIOLATION":
            task = replace(task, status="blocked")
        elif event_type == "ESCALATE_TO_HUMAN":
            task = replace(task, status="blocked")
            state = replace(state, status="blocked")
        else:
            _error("UNKNOWN_EVENT", f"event {event_type!r} is unsupported")
        state = _replace_task(state, _task_with_history(task, event))
    return _refresh_satisfaction(replace(state, events=state.events + (event,)))


def replay(batches: list[EventBatch] | tuple[EventBatch, ...]) -> RunState:
    """Verify and replay batches from genesis, with no I/O or mutable snapshots."""
    state = initial_state()
    previous: EventBatch | None = None
    for batch in batches:
        if not isinstance(batch, EventBatch):
            batch = EventBatch.from_dict(batch)
        else:
            batch = EventBatch.from_dict(batch.to_dict())
        verify_batch(previous, batch)
        for event in batch.events:
            if (event.event_type == "REQUEST_RESOLVED" and event.payload["request_id"] not in state.requests
                    and event.payload["expected_sequence"] != batch.sequence - 1):
                _error("REQUEST_CONFLICT", "unreserved resolution must bind the preceding batch head")
            state = reduce_event(state, event)
        created_at = state.created_at
        if created_at is None and any(event.event_type == "RUN_CREATED" for event in batch.events):
            created_at = batch.occurred_at
        state = replace(state, latest_sequence=batch.sequence, latest_hash=batch.batch_hash,
                        created_at=created_at, updated_at=batch.occurred_at)
        previous = batch
    return state
