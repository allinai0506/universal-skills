#!/usr/bin/env python3
"""Read-only structural/integrity checks. Never executes recorded commands.

Exit 0: mechanical checks passed; 1: incomplete/inconsistent evidence;
2: command-line or unreadable/invalid JSON input. Not a causal proof engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Optional

MAX_RECORD_BYTES = 2 * 1024 * 1024
PLACEHOLDERS = {"", "TODO", "TBD", "待填写", "未填写"}


def meaningful(value: Any) -> bool:
    return (isinstance(value, str) and value.strip() not in PLACEHOLDERS
            and not (value.strip().startswith("<") and value.strip().endswith(">")))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reject_duplicate_keys(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def validate(data: Any, root: Path, phase: str) -> list[str]:
    """Validate a record and files under root; no network, subprocess or writes."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["record must be an object"]
    root = root.resolve()
    if phase not in {"diagnose", "close"}:
        return ["phase must be diagnose or close"]

    def require(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    def obj(parent: dict, key: str) -> dict:
        value = parent.get(key)
        require(isinstance(value, dict), key + " must be an object")
        return value if isinstance(value, dict) else {}

    def text(parent: dict, key: str, prefix: str = "") -> None:
        require(meaningful(parent.get(key)), prefix + key + " must contain real text")

    def texts(parent: dict, key: str, allow_empty: bool = False) -> list:
        value = parent.get(key)
        ok = (isinstance(value, list) and (allow_empty or bool(value))
              and all(meaningful(x) for x in value))
        require(ok, key + " must be a list of real strings")
        return value if isinstance(value, list) else []

    require(type(data.get("schema_version")) is int and data["schema_version"] == 1,
            "schema_version must be integer 1")
    for key in ("id", "symptom"):
        text(data, key)
    require(data.get("mode") in ("diagnose", "fix", "review", "mitigate"), "invalid mode")
    require(data.get("risk") in ("standard", "high"), "risk must be standard or high")
    require(data.get("status") in ("supported", "fixed"),
            "record is not supported/fixed; unverified or mitigated work cannot pass")

    evidence = data.get("evidence")
    require(isinstance(evidence, list) and bool(evidence), "evidence must be non-empty list")
    index: dict[str, dict] = {}
    for i, item in enumerate(evidence if isinstance(evidence, list) else []):
        label = "evidence[" + str(i) + "]"
        if not isinstance(item, dict):
            errors.append(label + " must be an object")
            continue
        for key in ("id", "description", "path"):
            text(item, key, label + ".")
        eid = item.get("id")
        if meaningful(eid):
            require(eid not in index, "duplicate evidence id: " + eid)
            index[eid] = item
        require(item.get("kind") in ("contract", "code", "log", "diff", "observation"),
                label + ".kind is invalid")
        digest = item.get("sha256")
        require(isinstance(digest, str) and bool(re.fullmatch(r"[0-9a-f]{64}", digest)),
                label + ".sha256 must be 64 lowercase hex characters")
        raw_path = item.get("path")
        if not meaningful(raw_path):
            continue
        try:
            relative = Path(raw_path)
            if relative.is_absolute():
                raise ValueError("absolute paths are not allowed")
            resolved = (root / relative).resolve()
            resolved.relative_to(root)
            if not resolved.is_file():
                raise ValueError("not a readable regular file")
            require(sha256_file(resolved) == digest, label + ": sha256 mismatch")
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(label + ": missing/unsafe evidence path: " + str(exc))

    def refs(parent: dict, key: str, label: str, kinds: tuple = ()) -> None:
        values = parent.get(key)
        if not isinstance(values, list) or not values:
            errors.append(label + " needs non-empty evidence references")
            return
        valid = []
        for value in values:
            if not isinstance(value, str) or value not in index:
                errors.append(label + ": unknown evidence reference " + repr(value))
            else:
                valid.append(index[value])
        if kinds:
            require(any(x.get("kind") in kinds for x in valid),
                    label + " needs evidence of kind " + "/".join(kinds))

    expected = obj(data, "expected")
    text(expected, "statement", "expected.")
    refs(expected, "source_refs", "expected.source_refs", ("contract", "code"))
    reproduction = obj(data, "reproduction")
    for key in ("command", "environment", "version", "observed"):
        text(reproduction, key, "reproduction.")
    refs(reproduction, "evidence_refs", "reproduction", ("log", "observation"))

    cause = obj(data, "causality")
    for key in ("trigger", "mechanism", "last_good", "first_bad", "escape"):
        text(cause, key, "causality.")
    require(cause.get("status") == "supported", "causality.status must be supported")
    refs(cause, "evidence_refs", "causality")
    experiment = obj(cause, "experiment")
    for key in ("prediction", "intervention", "observation"):
        text(experiment, key, "experiment.")
    refs(experiment, "evidence_refs", "experiment", ("log", "observation"))
    impact = obj(data, "impact")
    for key in ("behaviors", "locations", "risks"):
        texts(impact, key)
    boundaries = texts(impact, "boundaries", allow_empty=True)

    if phase == "diagnose":
        return errors

    require(data.get("mode") in ("fix", "review"), "close requires fix or review mode")
    require(data.get("status") == "fixed", "close requires status=fixed")
    fix = obj(data, "fix")
    for key in ("summary", "version", "data_repair"):
        text(fix, key, "fix.")
    guard = obj(fix, "guard")
    for key in ("statement", "location", "scope"):
        text(guard, key, "guard.")
    refs(guard, "evidence_refs", "guard", ("code", "diff"))

    checks = data.get("checks")
    require(isinstance(checks, list) and bool(checks), "checks must be non-empty list")
    checks = checks if isinstance(checks, list) else []
    valid_checks = []
    seen: set[str] = set()
    for i, check in enumerate(checks):
        label = "checks[" + str(i) + "]"
        if not isinstance(check, dict):
            errors.append(label + " must be an object")
            continue
        for key in ("id", "case", "environment", "version", "command", "observation"):
            text(check, key, label + ".")
        cid = check.get("id")
        if meaningful(cid):
            require(cid not in seen, "duplicate check id: " + cid)
            seen.add(cid)
        require(check.get("kind") in ("regression", "neighbor", "integration", "counterfactual", "other"),
                label + ".kind is invalid")
        require(check.get("stage") in ("before", "after", "reintroduced"), label + ".stage is invalid")
        outcome, code = check.get("outcome"), check.get("exit_code")
        require(outcome in ("passed", "failed", "blocked", "not_run"), label + ".outcome is invalid")
        if outcome in ("passed", "failed"):
            require(type(code) is int and ((outcome == "passed" and code == 0)
                    or (outcome == "failed" and code != 0)), label + ": inconsistent exit code")
            refs(check, "evidence_refs", label, ("log", "observation"))
        else:
            require(code is None, label + ": blocked/not_run must use exit_code=null")
        if check.get("stage") == "after":
            require(outcome == "passed", label + ": required post-fix check did not pass")
        valid_checks.append(check)

    def selected(kind: str, stage: str, outcome: str) -> list[dict]:
        return [c for c in valid_checks if c.get("kind") == kind
                and c.get("stage") == stage and c.get("outcome") == outcome]

    reds = selected("regression", "before", "failed")
    greens = selected("regression", "after", "passed")
    pairs = [(r, g) for r in reds for g in greens
             if meaningful(r.get("case")) and r.get("case") == g.get("case")
             and meaningful(r.get("environment")) and r.get("environment") == g.get("environment")
             and meaningful(r.get("version")) and r.get("version") != g.get("version")
             and g.get("version") == fix.get("version")]
    require(bool(pairs), "need matched regression red/green: same case/environment, different versions, green=fix")
    for kind in (("neighbor", "integration") if boundaries else ("neighbor",)):
        require(any(c.get("version") == fix.get("version")
                    and any(c.get("environment") == g.get("environment") for _, g in pairs)
                    for c in selected(kind, "after", "passed")), "need passing fixed-version " + kind + " check")
    if data.get("risk") == "high":
        counters = selected("counterfactual", "reintroduced", "failed")
        require(any(c.get("case") == g.get("case") and c.get("environment") == g.get("environment")
                    and meaningful(c.get("version")) and c.get("version") != fix.get("version")
                    for c in counters for _, g in pairs),
                "high risk needs matched failing counterfactual with defect reintroduced")
    release = obj(data, "release")
    require(release.get("deployment") in ("not_deployed", "deployed", "unknown"), "invalid deployment state")
    for key in ("observation", "rollback"):
        text(release, key, "release.")
    texts(data, "limitations")
    return errors


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--phase", choices=("diagnose", "close"), default="diagnose")
    parser.add_argument("--evidence-root", type=Path,
                        help="Trusted root for relative evidence paths; default: record parent")
    args = parser.parse_args(argv)
    try:
        if args.record.stat().st_size > MAX_RECORD_BYTES:
            raise ValueError("JSON record exceeds 2 MiB")
        data = json.loads(args.record.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        errors = validate(data, args.evidence_root or args.record.resolve().parent, args.phase)
    except (OSError, ValueError, RecursionError, RuntimeError) as exc:
        print("INPUT ERROR: " + str(exc), file=sys.stderr)
        return 2
    if errors:
        print("FAIL: evidence checks")
        for error in errors:
            print("- " + error)
        return 1
    print("PASS: mechanical evidence checks only; causality, authenticity and coverage require review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
