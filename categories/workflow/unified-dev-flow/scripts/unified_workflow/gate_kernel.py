"""Pure command gates. Only the reducer interprets emitted state transitions.

INIT_RUN payload supplies the RouteContract persisted in RUN_CREATED. Observations
are either a WorkspaceRevision or a mapping with ``workspace`` and/or
``task_workspaces`` (task id -> revision). changed_paths is supplied by the provider
relative to the task's immutable scope_origin, not merely the latest command.
Review source fingerprints bind verification inputs; test fingerprints hash the
ordered verification command contracts; evidence fingerprints hash the ordered
fresh command evidence digests. Canonical record hashes exclude their own field.
"""
from __future__ import annotations

from fnmatch import fnmatchcase
from typing import Mapping

from .commands import Allowed, Command, Decision, Denied
from .events import DomainEvent
from .model import (DELIVERY_ORDER, EvidenceRecord, ReviewAssertion, RouteContract,
                    TaskContract, ValidationError, WorkspaceRevision, _json_plain,
                    canonical_sha256)
from .reducer import RunState, TaskState, reduce_event


def delivery_at_or_below_ceiling(target: str, ceiling: str) -> bool:
    return (target in DELIVERY_ORDER and ceiling in DELIVERY_ORDER
            and DELIVERY_ORDER.index(target) <= DELIVERY_ORDER.index(ceiling))


def dependency_closure(state: RunState, task_id: str) -> frozenset[str]:
    pending = list(state.tasks[task_id].contract.dependencies)
    found = set()
    while pending:
        identifier = pending.pop()
        if identifier in found:
            continue
        found.add(identifier)
        if identifier in state.tasks:
            pending.extend(state.tasks[identifier].contract.dependencies)
    return frozenset(found)


def scope_violations(task: TaskState, paths=()) -> tuple[str, ...]:
    def matches(parts, pattern):
        if not pattern:
            return not parts
        if pattern[0] == "**":
            return matches(parts, pattern[1:]) or bool(parts) and matches(parts[1:], pattern)
        return bool(parts) and fnmatchcase(parts[0], pattern[0]) and matches(parts[1:], pattern[1:])

    unresolved = False
    for event in task.history:
        if event.event_type == "SCOPE_VIOLATION":
            unresolved = True
        elif event.event_type == "TASK_UNBLOCKED" and event.payload.get("provenance"):
            unresolved = False
    violations = ["unresolved_scope_violation"] if unresolved else []
    for path in paths:
        parts = path.split("/")
        if (path.startswith("/") or ".." in parts or "\\" in path
                or parts[0] in (".git", ".unified-dev-flow")
                or any(matches(parts, pattern.split("/")) for pattern in task.contract.write_scope.forbidden_paths)
                or not any(matches(parts, pattern.split("/")) for pattern in task.contract.write_scope.allowed_paths)):
            violations.append(path)
    return tuple(violations)


def fresh_evidence(task: TaskState, workspace: WorkspaceRevision | None) -> tuple[EvidenceRecord, ...]:
    if workspace is None:
        return ()
    latest = {}
    for event in task.history:
        if event.event_type in ("TASK_INVALIDATED", "TASK_NEEDS_FIXES"):
            latest.clear()
        elif event.event_type == "VERIFICATION_RECORDED" and "evidence" in event.payload:
            evidence = EvidenceRecord.from_dict(_json_plain(event.payload["evidence"]))
            latest[evidence.command_id] = (event.payload["success"], evidence)
    fresh = []
    for verification in task.contract.verification_commands:
        item = latest.get(verification.command_id)
        if item is None:
            continue
        success, evidence = item
        unsigned = evidence.to_dict()
        unsigned.pop("evidence_sha256")
        revisions = (evidence.pre_command_revision, evidence.post_command_revision,
                     evidence.commit_revision, workspace)
        if (success and evidence.exit_code == 0 and not evidence.timed_out
                and not evidence.output_truncated
                and evidence.task_id == task.task_id
                and evidence.task_revision == task.task_revision
                and evidence.task_contract_sha256 == canonical_sha256(task.contract.to_dict())
                and evidence.command_sha256 == canonical_sha256(verification.to_dict())
                and evidence.evidence_sha256 == canonical_sha256(unsigned)
                and all(revision is not None and revision.provider == workspace.provider
                        and revision.revision_id == workspace.revision_id
                        and revision.verification_input_fingerprint == evidence.verification_input_fingerprint
                        for revision in revisions)
                and not scope_violations(task, evidence.scope_diff + workspace.changed_paths)):
            fresh.append(evidence)
    return tuple(fresh)


def fresh_review(task: TaskState, assertion: ReviewAssertion,
                 workspace: WorkspaceRevision | None) -> bool:
    unsigned = assertion.to_dict()
    unsigned.pop("assertion_sha256")
    return (workspace is not None and assertion.task_id == task.task_id
            and assertion.task_revision == task.task_revision
            and assertion.task_contract_sha256 == canonical_sha256(task.contract.to_dict())
            and assertion.source_fingerprint == workspace.verification_input_fingerprint
            and assertion.test_fingerprint == canonical_sha256(
                [item.to_dict() for item in task.contract.verification_commands])
            and assertion.evidence_fingerprint == canonical_sha256(
                [item.evidence_sha256 for item in fresh_evidence(task, workspace)])
            and assertion.assertion_sha256 == canonical_sha256(unsigned))


def acceptance_set_sha256(state: RunState) -> str:
    return canonical_sha256([
        {"task_id": task.task_id, "task_revision": task.task_revision,
         "input_fingerprint": task.accepted_input_fingerprint,
         "verdict_fingerprint": task.accepted_verdict_fingerprint}
        for task in sorted(state.tasks.values(), key=lambda item: item.task_id)
        if task.contract.required and task.currently_satisfied])


def _init_run(state, command, route, observations):
    if state.status != "new" or command.task_id is not None:
        return Decision((), Denied("INVALID_TRANSITION", ("Initialize a new run.",)))
    route = RouteContract.from_dict(_json_plain(command.payload["route"]))
    if route.delivery_target == "patch":
        return Decision((), Denied("RUNTIME_NOT_AUTHORIZED", ("Authorize working_tree or higher delivery.",)))
    if not delivery_at_or_below_ceiling(route.obligations.required_delivery, route.delivery_target):
        return Decision((), Denied("INVALID_CONTRACT", ("Align required delivery with authorization.",)))
    return Decision((DomainEvent("RUN_CREATED", {"work_id": command.work_id, "route": route.to_dict()}),), Allowed({}))


def _add_task(state, command, route, observations):
    task = TaskContract.from_dict(_json_plain(command.payload["task"]))
    if task.task_id != command.task_id or task.task_id in state.tasks:
        return Decision((), Denied("INVALID_CONTRACT", ("Supply a unique matching task id.",)))
    if task.task_id in task.dependencies or any(item not in state.tasks for item in task.dependencies):
        return Decision((), Denied("INVALID_CONTRACT", ("Declare existing acyclic dependencies.",)))
    return Decision((DomainEvent("TASK_ADDED", {"task": task.to_dict()}),), Allowed({}))


def _ready_task(state, command, route, observations):
    task = state.tasks[command.task_id]
    if scope_violations(task):
        return Decision((), Denied("SCOPE_VIOLATION", ("Resolve the scope blocker with provenance.",)))
    if task.status not in ("draft", "stale", "ready"):
        return Decision((), Denied("INVALID_TRANSITION", ("Ready a draft or stale task.",)))
    if any(identifier not in state.tasks or not state.tasks[identifier].currently_satisfied
           for identifier in dependency_closure(state, task.task_id)):
        return Decision((), Denied("DEPENDENCY_NOT_SATISFIED", ("Accept all current dependencies.",)))
    return Decision((DomainEvent("TASK_READIED", {"task_id": task.task_id}),), Allowed({}))


def _start_task(state, command, route, observations):
    task = state.tasks[command.task_id]
    if scope_violations(task):
        return Decision((), Denied("SCOPE_VIOLATION", ("Resolve the scope blocker with provenance.",)))
    if task.status != "ready" or any(item.status == "running" for item in state.tasks.values()):
        return Decision((), Denied("INVALID_TRANSITION", ("Start one ready writable task at a time.",)))
    if any(identifier not in state.tasks or not state.tasks[identifier].currently_satisfied
           for identifier in dependency_closure(state, task.task_id)):
        return Decision((), Denied("DEPENDENCY_NOT_SATISFIED", ("Accept all current dependencies.",)))
    workspace = observations.get(task.task_id)
    if workspace is None:
        return Decision((), Denied("EVIDENCE_MISSING", ("Observe the current workspace.",)))
    origin = task.scope_origin if task.scope_origin is not None else workspace.to_dict()
    return Decision((DomainEvent("TASK_STARTED", {"task_id": task.task_id, "scope_origin": origin}),), Allowed({}))


def _report_task(state, command, route, observations):
    task = state.tasks[command.task_id]
    if task.status != "running":
        return Decision((), Denied("INVALID_TRANSITION", ("Report a running task.",)))
    workspace = observations.get(task.task_id)
    report_revision = WorkspaceRevision.from_dict(_json_plain(command.payload["workspace_revision"]))
    report = command.payload["report"]
    if not isinstance(report, Mapping) or not isinstance(report.get("summary"), str) or not report["summary"]:
        return Decision((), Denied("INVALID_CONTRACT", ("Provide a nonempty report summary.",)))
    if (workspace is None or (workspace.provider, workspace.revision_id, workspace.verification_input_fingerprint)
            != (report_revision.provider, report_revision.revision_id, report_revision.verification_input_fingerprint)):
        return Decision((), Denied("EVIDENCE_STALE", ("Report the commit-time workspace revision.",)))
    if scope_violations(task, workspace.changed_paths):
        return Decision((DomainEvent("SCOPE_VIOLATION", {"task_id": task.task_id}),),
                        Denied("SCOPE_VIOLATION", ("Resolve changes outside the write scope.",)))
    return Decision((DomainEvent("TASK_REPORTED", {"task_id": task.task_id,
        "report": {**report, "workspace_revision": workspace.to_dict()}}),), Allowed({}))


def _record_verification(state, command, route, observations):
    task = state.tasks[command.task_id]
    if task.status != "running":
        return Decision((), Denied("INVALID_TRANSITION", ("Verify a running task.",)))
    evidence = EvidenceRecord.from_dict(_json_plain(command.payload["evidence"]))
    unsigned = evidence.to_dict()
    unsigned.pop("evidence_sha256")
    if evidence.evidence_sha256 != canonical_sha256(unsigned):
        return Decision((), Denied("INVALID_CONTRACT", ("Provide an intact evidence digest.",)))
    workspace = observations.get(task.task_id)
    scope = scope_violations(task, evidence.scope_diff + (() if workspace is None else workspace.changed_paths))
    event = DomainEvent("VERIFICATION_RECORDED", {"task_id": task.task_id,
                        "success": True, "evidence": evidence.to_dict()})
    candidate = reduce_event(state, event).tasks[task.task_id]
    fresh = any(item.evidence_sha256 == evidence.evidence_sha256 for item in fresh_evidence(candidate, workspace))
    if fresh:
        return Decision((event,), Allowed({"evidence_sha256": evidence.evidence_sha256}))
    failed = DomainEvent("VERIFICATION_RECORDED", {"task_id": task.task_id,
                         "success": False, "evidence": evidence.to_dict()})
    if scope:
        return Decision((failed, DomainEvent("SCOPE_VIOLATION", {"task_id": task.task_id})),
                        Denied("SCOPE_VIOLATION", ("Resolve verification side effects outside scope.",)))
    if evidence.exit_code != 0 or evidence.timed_out or evidence.output_truncated:
        return Decision((failed,), Denied("EVIDENCE_MISSING", ("Retry a successful bounded verification.",)))
    if workspace is None:
        return Decision((failed,), Denied("EVIDENCE_MISSING", ("Observe the current workspace before verifying freshness.",)))
    binding_valid = (evidence.task_id == task.task_id and evidence.task_revision == task.task_revision
        and evidence.task_contract_sha256 == canonical_sha256(task.contract.to_dict())
        and any(item.command_id == evidence.command_id and canonical_sha256(item.to_dict()) == evidence.command_sha256
                for item in task.contract.verification_commands))
    events = (failed,)
    if binding_valid and workspace.verification_input_fingerprint != evidence.verification_input_fingerprint:
        events += (DomainEvent("TASK_INVALIDATED", {"task_id": task.task_id,
                   "new_task_revision": task.task_revision + 1}),)
    return Decision(events, Denied("EVIDENCE_STALE", ("Reverify the current task and workspace.",)))


def _wait_for_review(state, command, route, observations):
    task = state.tasks[command.task_id]
    if task.status != "running":
        return Decision((), Denied("INVALID_TRANSITION", ("Verify a running task before review.",)))
    fresh = fresh_evidence(task, observations.get(task.task_id))
    identifiers = {item.command_id for item in fresh}
    claims = {claim for verification in task.contract.verification_commands
              if verification.command_id in identifiers for claim in verification.claims}
    if (any(item.required and item.command_id not in identifiers for item in task.contract.verification_commands)
            or not set(route.obligations.verification_claims).issubset(claims)):
        return Decision((), Denied("EVIDENCE_MISSING", ("Supply fresh passing evidence covering required commands and claims.",)))
    return Decision((DomainEvent("TASK_WAITING_REVIEW", {"task_id": task.task_id}),), Allowed({}))


def _record_review(state, command, route, observations):
    task = state.tasks[command.task_id]
    if task.status != "waiting_review":
        return Decision((), Denied("INVALID_TRANSITION", ("Wait for review before recording a verdict.",)))
    assertion = ReviewAssertion.from_dict(_json_plain(command.payload["assertion"]))
    if assertion.provenance not in route.obligations.accepted_review_provenance:
        return Decision((), Denied("PROVENANCE_INSUFFICIENT", ("Supply an allowed review provenance.",)))
    if not fresh_review(task, assertion, observations.get(task.task_id)):
        return Decision((), Denied("VERDICT_STALE", ("Review current inputs, tests, and evidence.",)))
    events = [DomainEvent("REVIEW_RECORDED", {"task_id": task.task_id,
        "verdict_fingerprint": assertion.assertion_sha256, "assertion": assertion.to_dict()})]
    if assertion.verdict == "NEEDS_FIXES" and task.review_round + 1 >= min(route.review_limit, 3):
        events.extend((DomainEvent("TASK_INVALIDATED", {"task_id": task.task_id,
            "new_task_revision": task.task_revision}),
            DomainEvent("TASK_BLOCKED", {"task_id": task.task_id, "review_round": task.review_round + 1}), DomainEvent("RUN_BLOCKED", {}),
            DomainEvent("ESCALATE_TO_HUMAN", {"task_id": task.task_id})))
        return Decision(tuple(events), Denied("REVIEW_LIMIT_REACHED", ("Resolve the review blocker with human provenance.",)))
    if assertion.verdict == "NEEDS_FIXES":
        events.append(DomainEvent("TASK_NEEDS_FIXES", {"task_id": task.task_id}))
    elif assertion.verdict == "ESCALATE":
        events.extend((DomainEvent("TASK_BLOCKED", {"task_id": task.task_id}),
                       DomainEvent("RUN_BLOCKED", {}), DomainEvent("ESCALATE_TO_HUMAN", {"task_id": task.task_id})))
    return Decision(tuple(events), Allowed({}))


def _accept_task(state, command, route, observations):
    task = state.tasks[command.task_id]
    if task.status != "waiting_review":
        return Decision((), Denied("INVALID_TRANSITION", ("Accept a task waiting for review.",)))
    if not task.reviews or "assertion" not in task.reviews[-1]:
        return Decision((), Denied("VERDICT_MISSING", ("Record a MERGE_READY review assertion.",)))
    assertion = ReviewAssertion.from_dict(_json_plain(task.reviews[-1]["assertion"]))
    if assertion.provenance not in route.obligations.accepted_review_provenance:
        return Decision((), Denied("PROVENANCE_INSUFFICIENT", ("Supply an allowed review provenance.",)))
    workspace = observations.get(task.task_id)
    if (assertion.verdict != "MERGE_READY" or task.current_fresh_verdict_fingerprint != assertion.assertion_sha256
            or not fresh_review(task, assertion, workspace)):
        return Decision((), Denied("VERDICT_STALE", ("Record a fresh MERGE_READY review assertion.",)))
    fresh = fresh_evidence(task, workspace)
    identifiers = {item.command_id for item in fresh}
    claims = {claim for item in task.contract.verification_commands if item.command_id in identifiers for claim in item.claims}
    if (any(item.required and item.command_id not in identifiers for item in task.contract.verification_commands)
            or not set(route.obligations.verification_claims).issubset(claims)):
        return Decision((), Denied("EVIDENCE_MISSING", ("Reverify all current obligations.",)))
    if any(not state.tasks[identifier].currently_satisfied for identifier in dependency_closure(state, task.task_id)):
        return Decision((), Denied("DEPENDENCY_NOT_SATISFIED", ("Accept current dependencies.",)))
    return Decision((DomainEvent("TASK_ACCEPTED", {"task_id": task.task_id,
        "input_fingerprint": workspace.verification_input_fingerprint,
        "verdict_fingerprint": assertion.assertion_sha256}),), Allowed({}))


def _resolve_blocker(state, command, route, observations):
    task = state.tasks[command.task_id]
    if task.status != "blocked" and not scope_violations(task):
        return Decision((), Denied("INVALID_TRANSITION", ("Resolve an existing blocker.",)))
    provenance = command.payload.get("provenance")
    if (not isinstance(provenance, Mapping) or not isinstance(provenance.get("actor"), str)
            or not provenance["actor"] or not isinstance(provenance.get("resolution"), str)
            or not provenance["resolution"]):
        return Decision((), Denied("PROVENANCE_INSUFFICIENT", ("Record who resolved the blocker and how.",)))
    events = [DomainEvent("TASK_UNBLOCKED", {"task_id": task.task_id, "provenance": provenance})]
    if state.status == "blocked" and not any(item.task_id != task.task_id and item.status == "blocked" for item in state.tasks.values()):
        events.append(DomainEvent("RUN_RESUMED", {}))
    return Decision(tuple(events), Allowed({}))


def _record_delivery(state, command, route, observations):
    target = command.payload["delivery_target"]
    if not delivery_at_or_below_ceiling(target, route.delivery_target):
        return Decision((), Denied("DELIVERY_NOT_AUTHORIZED", ("Stay within the authorized delivery ceiling.",)))
    if command.payload["acceptance_set_sha256"] != acceptance_set_sha256(state):
        return Decision((), Denied("EVIDENCE_STALE", ("Bind delivery to the current acceptance set.",)))
    if any(task.contract.required and not task.currently_satisfied for task in state.tasks.values()):
        return Decision((), Denied("DEPENDENCY_NOT_SATISFIED", ("Accept all required tasks before delivery.",)))
    provenance = command.payload["provenance"]
    if not isinstance(provenance, Mapping) or not provenance.get("provider") or not provenance.get("reference"):
        return Decision((), Denied("PROVENANCE_INSUFFICIENT", ("Provide delivery provider and verifiable reference.",)))
    revision = WorkspaceRevision.from_dict(_json_plain(command.payload["workspace_revision"]))
    required = {task.task_id for task in state.tasks.values() if task.contract.required}
    for identifier in tuple(required):
        required.update(dependency_closure(state, identifier))
    if (not observations or not required.issubset(observations)
            or any((item.provider, item.revision_id, item.verification_input_fingerprint) !=
                   (revision.provider, revision.revision_id, revision.verification_input_fingerprint)
                   for item in observations.values())):
        return Decision((), Denied("EVIDENCE_STALE", ("Bind delivery to the current workspace revision.",)))
    return Decision((DomainEvent("DELIVERY_RECORDED", dict(command.payload)),), Allowed({}))


def _complete_run(state, command, route, observations):
    if state.status == "blocked" or any(task.status == "blocked" or scope_violations(task) for task in state.tasks.values()):
        return Decision((), Denied("INVALID_TRANSITION", ("Resolve outstanding blockers.",)))
    if any(task.contract.required and not task.currently_satisfied for task in state.tasks.values()):
        return Decision((), Denied("DEPENDENCY_NOT_SATISFIED", ("Accept every required task at its current revision.",)))
    required = {task.task_id for task in state.tasks.values() if task.contract.required}
    for identifier in tuple(required):
        required.update(dependency_closure(state, identifier))
    if not required.issubset(observations):
        return Decision((), Denied("EVIDENCE_MISSING", ("Observe every required task before completion.",)))
    current = acceptance_set_sha256(state)
    if not any(item["acceptance_set_sha256"] == current
               and delivery_at_or_below_ceiling(route.obligations.required_delivery, item["delivery_target"])
               and delivery_at_or_below_ceiling(item["delivery_target"], route.delivery_target)
               and item.get("workspace_revision") and item.get("provenance") for item in state.deliveries):
        return Decision((), Denied("EVIDENCE_MISSING", ("Record delivery bound to the current acceptance set.",)))
    return Decision((DomainEvent("RUN_COMPLETED", {}),), Allowed({}))


def _cancel_task(state, command, route, observations):
    task = state.tasks[command.task_id]
    if task.status == "cancelled":
        return Decision((), Denied("INVALID_TRANSITION", ("Cancel an active task.",)))
    return Decision((DomainEvent("TASK_CANCELLED", {"task_id": task.task_id}),), Allowed({}))


def _cancel_run(state, command, route, observations):
    events = tuple(DomainEvent("TASK_CANCELLED", {"task_id": task.task_id})
                   for task in state.tasks.values() if task.status not in ("accepted", "cancelled"))
    return Decision(events + (DomainEvent("RUN_CANCELLED", {}),), Allowed({}))


_HANDLERS = {"INIT_RUN": _init_run, "ADD_TASK": _add_task, "READY_TASK": _ready_task,
    "START_TASK": _start_task, "REPORT_TASK": _report_task, "RECORD_VERIFICATION": _record_verification,
    "WAIT_FOR_REVIEW": _wait_for_review, "RECORD_REVIEW": _record_review, "ACCEPT_TASK": _accept_task,
    "RESOLVE_BLOCKER": _resolve_blocker, "RECORD_DELIVERY": _record_delivery,
    "COMPLETE_RUN": _complete_run, "CANCEL_TASK": _cancel_task, "CANCEL_RUN": _cancel_run}

_PAYLOAD_FIELDS = {"INIT_RUN": {"route"}, "ADD_TASK": {"task"},
    "REPORT_TASK": {"report", "workspace_revision"}, "RECORD_VERIFICATION": {"evidence"},
    "RECORD_REVIEW": {"assertion"}, "RESOLVE_BLOCKER": {"provenance"},
    "RECORD_DELIVERY": {"delivery_target", "acceptance_set_sha256", "workspace_revision", "provenance"}}


def decide(state: RunState, command: Command, observed_facts=None) -> Decision:
    """Return domain events plus outcome without performing I/O or changing state.

    Request identity, sequence, lock and hash-chain failures belong to Store.
    Missing observations never establish fresh evidence or a fresh verdict.
    """
    try:
        command = Command.from_dict(command.to_dict())
        if set(command.payload) - _PAYLOAD_FIELDS.get(command.command_type, set()):
            raise ValidationError("UNKNOWN_FIELD", "Unsupported command payload fields")
        route = None
        observations = {}
        if isinstance(observed_facts, WorkspaceRevision):
            observations = {identifier: observed_facts for identifier in state.tasks}
        elif observed_facts is not None:
            if not isinstance(observed_facts, Mapping) or set(observed_facts) - {"workspace", "task_workspaces"}:
                raise ValidationError("INVALID_TYPE", "Unsupported observations")
            if "workspace" in observed_facts:
                observations = {identifier: observed_facts["workspace"] for identifier in state.tasks}
            observations.update(observed_facts.get("task_workspaces", {}))
        observations = {identifier: WorkspaceRevision.from_dict(
            item.to_dict() if isinstance(item, WorkspaceRevision) else _json_plain(item))
            for identifier, item in observations.items()}
        if command.command_type == "INIT_RUN":
            return _init_run(state, command, route, observations)
        if state.status in ("new", "completed", "cancelled") or command.work_id != state.work_id:
            return Decision((), Denied("INVALID_TRANSITION", ("Use an active matching run.",)))
        for event in state.events:
            if event.event_type == "RUN_CREATED" and "route" in event.payload:
                route = RouteContract.from_dict(_json_plain(event.payload["route"]))
                break
        if route is None:
            return Decision((), Denied("INVALID_CONTRACT", ("Initialize the run with a RouteContract.",)))
        task_commands = set(_HANDLERS) - {"INIT_RUN", "ADD_TASK", "RECORD_DELIVERY", "COMPLETE_RUN", "CANCEL_RUN"}
        if command.command_type in task_commands and command.task_id not in state.tasks:
            return Decision((), Denied("INVALID_TRANSITION", ("Address an existing task.",)))
        if state.status == "blocked" and command.command_type not in ("RESOLVE_BLOCKER", "CANCEL_TASK", "CANCEL_RUN", "COMPLETE_RUN"):
            return Decision((), Denied("INVALID_TRANSITION", ("Resolve the run blocker first.",)))
        invalidations = []
        if command.command_type not in ("CANCEL_TASK", "CANCEL_RUN", "RESOLVE_BLOCKER", "RECORD_VERIFICATION"):
            for identifier, workspace in sorted(observations.items()):
                task = state.tasks.get(identifier)
                if (task is not None and task.scope_origin is not None
                        and (task.status in ("running", "waiting_review")
                             or task.status == "accepted" and command.command_type in ("RECORD_DELIVERY", "COMPLETE_RUN"))
                        and scope_violations(task, workspace.changed_paths)):
                    return Decision((DomainEvent("SCOPE_VIOLATION", {"task_id": identifier}),),
                                    Denied("SCOPE_VIOLATION", ("Resolve changes outside the write scope.",)))
            projected = state
            for identifier, workspace in sorted(observations.items()):
                task = projected.tasks.get(identifier)
                if task is None or task.status not in ("accepted", "waiting_review", "running"):
                    continue
                fingerprint = task.accepted_input_fingerprint
                if fingerprint is None:
                    for fact in task.history:
                        if fact.event_type in ("TASK_INVALIDATED", "TASK_NEEDS_FIXES"):
                            fingerprint = None
                        elif (fact.event_type == "VERIFICATION_RECORDED" and fact.payload["success"]
                              and "evidence" in fact.payload):
                            fingerprint = fact.payload["evidence"]["verification_input_fingerprint"]
                if fingerprint is not None and fingerprint != workspace.verification_input_fingerprint:
                    event = DomainEvent("TASK_INVALIDATED", {"task_id": identifier, "new_task_revision": task.task_revision + 1})
                    invalidations.append(event)
                    projected = reduce_event(projected, event)
            if invalidations:
                return Decision(tuple(invalidations), Denied("EVIDENCE_STALE", ("Revalidate invalidated tasks and dependents.",)))
        return _HANDLERS[command.command_type](state, command, route, observations)
    except (ValidationError, KeyError, TypeError, AttributeError) as exc:
        return Decision((), Denied("INVALID_CONTRACT", (f"Correct the command contract: {exc}",)))
