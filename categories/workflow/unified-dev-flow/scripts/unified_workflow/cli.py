"""Thin argparse boundary over Store, Gate commands, and the trusted local Provider."""
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass, replace
import json
from pathlib import Path
import sys

from .commands import Allowed, Command
from .events import IntegrityError
from .model import (ReviewAssertion, RouteContract, TaskContract, ValidationError,
                    WorkspaceRevision, canonical_sha256, validate_id)
from .providers.base import ProviderError
from .providers.trusted_local import TrustedLocalVerifier
from .reducer import initial_state
from .store import ObserveRequest, RunStore


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValidationError("INVALID_ARGUMENTS", message)


def _parser():
    common = Parser(add_help=False, argument_default=argparse.SUPPRESS)
    common.add_argument("--project-root")
    common.add_argument("--work-id")
    common.add_argument("--json", action="store_true")
    parser = Parser(prog="unified-workflow", parents=[common],
                    description="Pin a Router contract and enforce local execution gates.")
    commands = parser.add_subparsers(dest="command", required=True)

    def leaf(owner, name, operation, *, mutation=True, task=False, document=None):
        item = owner.add_parser(name, parents=[common])
        item.set_defaults(operation=operation)
        if mutation:
            item.add_argument("--request-id", required=True)
            item.add_argument("--expected-sequence", type=int)
            item.add_argument("--actor-file")
        if task:
            item.add_argument("--task-id", required=True)
        if document:
            item.add_argument("--" + document + "-file", required=True)
        return item

    def group(name):
        return commands.add_parser(name, parents=[common]).add_subparsers(required=True)

    leaf(commands, "init", "INIT_RUN", document="route")
    task = group("task")
    leaf(task, "add", "ADD_TASK", document="task")
    for name, operation in (("ready", "READY_TASK"), ("start", "START_TASK"), ("accept", "ACCEPT_TASK")):
        leaf(task, name, operation, task=True)
    leaf(task, "report", "REPORT_TASK", task=True, document="report")
    leaf(task, "resolve-blocker", "RESOLVE_BLOCKER", task=True, document="provenance")
    leaf(commands, "verify", "RECORD_VERIFICATION", task=True).add_argument("--command-id", required=True)
    leaf(group("review"), "record", "RECORD_REVIEW", task=True, document="assertion")
    leaf(group("delivery"), "record", "RECORD_DELIVERY", document="delivery")
    leaf(group("run"), "complete", "COMPLETE_RUN")
    for name in ("status", "replay"):
        leaf(commands, name, "READ_STATE", mutation=False)
    request = group("request")
    leaf(request, "status", "READ_REQUEST", mutation=False).add_argument("--request-id", required=True)
    leaf(request, "resolve", "RESOLVE_REQUEST", document="resolution")
    return parser


def _document(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValidationError("INVALID_JSON", "Duplicate JSON object key")
            result[key] = value
        return result

    def constant(_value):
        raise ValidationError("INVALID_JSON", "JSON must contain finite values")

    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                           parse_constant=constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError("INVALID_JSON_FILE", "Cannot read a valid UTF-8 JSON document") from exc
    if not isinstance(value, dict):
        raise ValidationError("INVALID_TYPE", "JSON document must be an object")
    return value


def _plain(value):
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _payload(args):
    if args.operation == "INIT_RUN":
        return {"route": RouteContract.from_dict(_document(args.route_file)).to_dict()}
    if args.operation == "ADD_TASK":
        task = TaskContract.from_dict(_document(args.task_file))
        args.task_id = task.task_id
        return {"task": task.to_dict()}
    if args.operation == "RECORD_REVIEW":
        return {"assertion": ReviewAssertion.from_dict(_document(args.assertion_file)).to_dict()}
    if args.operation == "RESOLVE_BLOCKER":
        return {"provenance": _document(args.provenance_file)}
    if args.operation == "REPORT_TASK":
        return _document(args.report_file)
    if args.operation == "RECORD_DELIVERY":
        return _document(args.delivery_file)
    if args.operation == "RECORD_VERIFICATION":
        return {"command_id": validate_id(args.command_id, "command_id")}
    return {}


def _observations(root, state):
    observations = {}
    for identifier, task in state.tasks.items():
        provider = TrustedLocalVerifier(root, task.contract)
        if task.scope_origin is None:
            # Bootstrap only the initial manifest; no task state or evidence is emitted here.
            empty = WorkspaceRevision.from_dict(dict(schema_version=1, provider=provider.name,
                revision_id="initial", verification_input_fingerprint=canonical_sha256({}),
                changed_paths=[], observed_at="1970-01-01T00:00:00Z", file_manifest={}))
            origin = provider.observe_workspace(ObserveRequest(task.contract, empty))
        else:
            origin = WorkspaceRevision.from_dict(_plain(task.scope_origin))
        observations[identifier] = provider.observe_workspace(ObserveRequest(task.contract, origin))
    return {"task_workspaces": observations}


def _result(result, *, verification=False, unregistered=False, resolution=False):
    if resolution and result.status in ("success", "denied", "provider_failure", "abandoned"):
        if result.state is not None and isinstance(result.outcome, Allowed):
            return 0, {"status": "success", "result": result.outcome.to_dict()["result"]}
        if getattr(result.outcome, "reason_code", "") in ("REQUEST_DENIED", "REQUEST_PROVIDER_FAILURE", "REQUEST_ABANDONED"):
            return 0, {"status": "success", "result": {"outcome": result.status}}
    if isinstance(result.outcome, Allowed):
        return 0, {"status": "success", "result": result.outcome.to_dict()["result"]}
    code = result.outcome.reason_code
    exit_code = {"INVALID_CONTRACT": 2, "LOCK_BUSY": 5, "PROVIDER_FAILURE": 6,
                 "REQUEST_IN_DOUBT": 7}.get(code, 3)
    if result.status == "provider_failure" or verification and (
            (unregistered and code == "INVALID_CONTRACT") or code == "EVIDENCE_MISSING"):
        exit_code = 6
    return exit_code, {"status": "error", **result.outcome.to_dict()}


def _execute(args):
    work_id = validate_id(getattr(args, "work_id", None), "work_id")
    root = Path(getattr(args, "project_root", "."))
    actor = _document(args.actor_file) if getattr(args, "actor_file", None) else {"type": "cli", "id": "local"}
    payload = _payload(args)
    if getattr(args, "expected_sequence", None) is not None and args.expected_sequence < 0:
        raise ValidationError("INVALID_ARGUMENTS", "expected-sequence must be nonnegative")
    if hasattr(args, "request_id"):
        validate_id(args.request_id, "request_id")
    store = RunStore(root, work_id)
    # A patch init must reach Store's no-write Gate preflight before any load.
    patch_init = args.operation == "INIT_RUN" and payload["route"]["delivery_target"] == "patch"
    try:
        state = initial_state() if patch_init else store.load()
    except ValidationError as exc:
        if exc.code == "UNSAFE_CONTROL_PATH":
            raise
        raise IntegrityError(exc.code, exc.message) from exc
    if args.operation == "READ_STATE":
        return 0, {"status": "success", "sequence": store.sequence,
                   "state": _plain(state), "diagnostics": list(store.diagnostics)}
    if args.operation == "READ_REQUEST":
        request = state.requests.get(args.request_id)
        if request is None:
            raise ValidationError("REQUEST_NOT_FOUND", "No reservation exists for this request ID")
        return (7 if request.status == "in_doubt" else 0), {
            "status": "in_doubt" if request.status == "in_doubt" else "success", "request": _plain(request)}
    if args.operation == "RESOLVE_REQUEST":
        document = _document(args.resolution_file)
        if set(document) != {"outcome", "actor", "note"} or not isinstance(document["actor"], dict) or not document["actor"]:
            raise ValidationError("INVALID_CONTRACT", "Resolution requires outcome, nonempty actor, and note")
        result = store.resolve_request(args.request_id, document["outcome"], document["actor"],
                                       document["note"], expected_sequence=args.expected_sequence)
        return _result(result, resolution=True)

    prior = state.requests.get(args.request_id)
    sequence = args.expected_sequence
    if sequence is None:
        sequence = prior.reservation_sequence - 1 if prior else store.sequence
    wait_id = "review-wait-" + canonical_sha256(args.request_id).removeprefix("sha256:")
    waited = state.requests.get(wait_id) if args.operation == "RECORD_REVIEW" else None
    if prior is not None and waited is not None and args.expected_sequence is not None:
        sequence += 1
    cmd = Command.from_dict(dict(schema_version=1, request_id=args.request_id, command_type=args.operation,
        work_id=work_id, task_id=getattr(args, "task_id", None), actor=actor,
        expected_sequence=sequence, payload=payload))
    if args.operation == "RECORD_VERIFICATION":
        task = state.tasks.get(args.task_id)
        # Store rejects a missing task/command before consulting the Provider.
        provider = TrustedLocalVerifier(root, task.contract) if task else None
        unregistered = task is not None and args.command_id not in {c.command_id for c in task.contract.verification_commands}
        return _result(store.execute_verification(cmd, provider), verification=True, unregistered=unregistered)
    if prior is not None:
        return _result(store.execute(cmd))
    facts = None if patch_init else _observations(root, state)
    if args.operation == "RECORD_REVIEW" and args.task_id in state.tasks:
        if state.tasks[args.task_id].status == "running" or waited is not None:
            wait_sequence = waited.reservation_sequence - 1 if waited and args.expected_sequence is None else sequence
            wait = replace(cmd, command_type="WAIT_FOR_REVIEW", request_id=wait_id,
                           expected_sequence=wait_sequence, payload={})
            outcome = store.execute(wait, facts)
            if not isinstance(outcome.outcome, Allowed):
                return _result(outcome)
            cmd = replace(cmd, expected_sequence=wait_sequence + 1)
            # Observe again after the separately durable wait gate.
            facts = _observations(root, outcome.state)
    return _result(store.execute(cmd, facts))


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        args = _parser().parse_args(arguments)
        code, output = _execute(args)
    except (ValidationError, IntegrityError, ProviderError) as exc:
        code = 5 if exc.code == "LOCK_BUSY" else 4 if isinstance(exc, IntegrityError) else 6 if isinstance(exc, ProviderError) else 2
        output = {"status": "error", "reason_code": exc.code, "required_actions": [exc.message]}
    except OSError:
        code, output = 6, {"status": "error", "reason_code": "IO_FAILURE",
                           "required_actions": ["Check project and filesystem access."]}
    if "--json" in arguments:
        # Histories can legitimately repeat events; protocol contract validation
        # rejects duplicate list values and must not be reapplied to read views.
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))
    elif "reason_code" in output:
        print(output["reason_code"] + ": " + " ".join(output["required_actions"]))
    else:
        print(output["status"] + (": " + output["state"]["status"] if "state" in output else ""))
    return code
