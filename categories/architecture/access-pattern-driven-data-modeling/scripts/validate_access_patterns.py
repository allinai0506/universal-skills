#!/usr/bin/env python3
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("FAIL: PyYAML is required. Install with: pip install pyyaml")
    raise SystemExit(2)

REQUIRED = ["name", "type", "purpose", "filters", "frequency", "expected_result_size"]

def main():
    if len(sys.argv) != 2:
        print("Usage: validate_access_patterns.py <yaml-file>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"FAIL: file not found: {path}")
        return 1

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: invalid YAML: {exc}")
        return 1

    if not isinstance(data, dict) or not isinstance(data.get("operations"), list):
        print("FAIL: root must contain an 'operations' list")
        return 1

    operations = data["operations"]
    if not operations:
        print("FAIL: no access patterns found")
        return 1

    errors = []
    warnings = []

    for i, op in enumerate(operations, 1):
        if not isinstance(op, dict):
            errors.append(f"operation[{i}] is not an object")
            continue

        for key in REQUIRED:
            # write operations may legitimately have empty filters
            if key == "filters" and op.get("type") == "write":
                continue
            if key not in op or op[key] in (None, "", []):
                errors.append(f"operation[{i}] missing required field: {key}")

        if op.get("type") not in ("read", "write"):
            errors.append(f"operation[{i}] type must be read or write")

        for key in ("expected_data_volume", "freshness", "consistency"):
            if key not in op:
                warnings.append(f"operation[{i}] omitted optional field: {key}")

        for key in ("frequency", "expected_result_size"):
            if op.get(key) == "UNKNOWN":
                warnings.append(f"operation[{i}] has UNKNOWN {key}")

    if errors:
        print("FAIL")
        for e in errors:
            print("-", e)
        return 1

    print("PASS")
    print(f"Validated access patterns: {len(operations)}")
    for w in warnings:
        print("WARNING:", w)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
