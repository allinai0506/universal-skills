#!/usr/bin/env python3
"""Validate an Ontology-as-Code directory.

Dependencies: PyYAML
Usage: python scripts/ontology_validate.py ontology
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
import yaml

CATEGORIES = {
    "objects": "object",
    "relations": "relation",
    "states": "state",
    "rules": "rule",
    "actions": "action",
    "policies": "policy",
    "workflows": "workflow",
    "connectors": "connector",
    "mappings": "mapping",
    "projections": "projection",
}
VALID_LIFECYCLES = {"experimental", "active", "deprecated"}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("top-level YAML must be a mapping")
    return data


def each_yaml(folder: Path):
    if not folder.exists():
        return
    for p in sorted(folder.rglob("*.y*ml")):
        if p.is_file():
            yield p


def req(data: dict[str, Any], fields: list[str], path: Path, errors: list[str]):
    for f in fields:
        if f not in data or data[f] in (None, ""):
            errors.append(f"{path}: missing required field '{f}'")


def main(root_arg: str) -> int:
    root = Path(root_arg).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    if not root.exists():
        print(f"ERROR: ontology root not found: {root}")
        return 2

    manifest = root / "ontology.yaml"
    if not manifest.exists():
        errors.append(f"{manifest}: missing ontology manifest")

    registry: dict[str, dict[str, tuple[Path, dict[str, Any]]]] = {k: {} for k in CATEGORIES}
    global_ids: dict[str, Path] = {}

    for folder in CATEGORIES:
        for path in each_yaml(root / folder) or []:
            try:
                data = load_yaml(path)
            except Exception as e:
                errors.append(f"{path}: invalid YAML: {e}")
                continue
            req(data, ["id", "name", "lifecycle"], path, errors)
            item_id = data.get("id")
            if isinstance(item_id, str) and item_id:
                if item_id in global_ids:
                    errors.append(f"{path}: duplicate id '{item_id}', first seen at {global_ids[item_id]}")
                else:
                    global_ids[item_id] = path
                registry[folder][item_id] = (path, data)
            lifecycle = data.get("lifecycle")
            if lifecycle not in VALID_LIFECYCLES:
                errors.append(f"{path}: lifecycle must be one of {sorted(VALID_LIFECYCLES)}")

    objects = registry["objects"]
    relations = registry["relations"]
    states = registry["states"]
    rules = registry["rules"]
    actions = registry["actions"]
    policies = registry["policies"]
    connectors = registry["connectors"]

    # Object checks
    for oid, (path, data) in objects.items():
        req(data, ["description", "identity", "properties", "evidence"], path, errors)
        if data.get("lifecycle") == "active" and not data.get("evidence"):
            errors.append(f"{path}: active object requires at least one evidence entry")

    # Relation checks
    for rid, (path, data) in relations.items():
        req(data, ["from", "to", "cardinality", "object_backed", "evidence"], path, errors)
        for key in ("from", "to"):
            ref = data.get(key)
            if ref and ref not in objects:
                errors.append(f"{path}: relation {key} references unknown object '{ref}'")

    # State checks
    for sid, (path, data) in states.items():
        req(data, ["object", "initial", "states", "transitions"], path, errors)
        obj = data.get("object")
        if obj and obj not in objects:
            errors.append(f"{path}: state machine references unknown object '{obj}'")
        declared = set(data.get("states") or [])
        if data.get("initial") not in declared:
            errors.append(f"{path}: initial state '{data.get('initial')}' is not declared")
        for t in data.get("terminal") or []:
            if t not in declared:
                errors.append(f"{path}: terminal state '{t}' is not declared")
        for tr in data.get("transitions") or []:
            if not isinstance(tr, dict):
                errors.append(f"{path}: each transition must be a mapping")
                continue
            if tr.get("from") not in declared or tr.get("to") not in declared:
                errors.append(f"{path}: transition {tr.get('from')} -> {tr.get('to')} uses undeclared state")
            for guard in tr.get("guards") or []:
                if guard not in rules:
                    errors.append(f"{path}: transition guard references unknown rule '{guard}'")

    # Rule checks
    for rid, (path, data) in rules.items():
        req(data, ["description", "inputs", "returns", "logic_ref", "evidence"], path, errors)
        for obj in data.get("inputs") or []:
            if obj not in objects:
                warnings.append(f"{path}: rule input '{obj}' is not a declared object")

    # Policy checks
    for pid, (path, data) in policies.items():
        req(data, ["subjects", "resources", "allowed_actions", "agent_execution"], path, errors)
        for a in data.get("allowed_actions") or []:
            if a not in actions:
                # second pass; actions registry already loaded
                errors.append(f"{path}: policy references unknown action '{a}'")

    # Action checks
    mandatory_action_fields = [
        "target", "inputs", "preconditions", "authorization", "effects",
        "side_effects", "idempotency", "transaction", "audit",
        "failure_behavior", "bindings", "verification"
    ]
    for aid, (path, data) in actions.items():
        req(data, mandatory_action_fields, path, errors)
        target = data.get("target")
        if target and target not in objects:
            errors.append(f"{path}: action target references unknown object '{target}'")
        for r in data.get("preconditions") or []:
            if r not in rules:
                errors.append(f"{path}: action precondition references unknown rule '{r}'")
        auth = data.get("authorization") or {}
        if isinstance(auth, dict):
            for p in auth.get("policies") or []:
                if p not in policies:
                    errors.append(f"{path}: action authorization references unknown policy '{p}'")
        for b in data.get("bindings") or []:
            if isinstance(b, dict):
                c = b.get("connector")
                if c and c not in connectors:
                    errors.append(f"{path}: action binding references unknown connector '{c}'")
        if data.get("lifecycle") == "active" and not data.get("bindings"):
            errors.append(f"{path}: active action requires at least one runtime binding")

    # Workflow refs
    for wid, (path, data) in registry["workflows"].items():
        req(data, ["trigger", "steps"], path, errors)
        for step in data.get("steps") or []:
            if not isinstance(step, dict):
                errors.append(f"{path}: workflow step must be a mapping")
                continue
            typ, ref = step.get("type"), step.get("ref")
            if typ == "action" and ref not in actions:
                errors.append(f"{path}: workflow step references unknown action '{ref}'")
            if typ == "rule" and ref not in rules:
                errors.append(f"{path}: workflow step references unknown rule '{ref}'")

    # Mapping refs
    for mid, (path, data) in registry["mappings"].items():
        req(data, ["object", "source", "fields", "authority"], path, errors)
        if data.get("object") not in objects:
            errors.append(f"{path}: mapping references unknown object '{data.get('object')}'")

    # Projection refs
    for prid, (path, data) in registry["projections"].items():
        req(data, ["consumers", "objects", "exclude_by_default"], path, errors)
        obj_block = data.get("objects") or {}
        if isinstance(obj_block, dict):
            for o in obj_block:
                if o not in objects:
                    errors.append(f"{path}: projection references unknown object '{o}'")
        for rel in data.get("relations") or []:
            if rel not in relations:
                errors.append(f"{path}: projection references unknown relation '{rel}'")
        for rule in data.get("rules") or []:
            if rule not in rules:
                errors.append(f"{path}: projection references unknown rule '{rule}'")
        for action in data.get("actions") or []:
            if action not in actions:
                errors.append(f"{path}: projection references unknown action '{action}'")
        for policy in data.get("policies") or []:
            if policy not in policies:
                errors.append(f"{path}: projection references unknown policy '{policy}'")

    print(f"Ontology root: {root}")
    print("Counts:")
    for k in CATEGORIES:
        print(f"  {k}: {len(registry[k])}")
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  - {e}")
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print("PASSED")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ontology_validate.py <ontology-root>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
