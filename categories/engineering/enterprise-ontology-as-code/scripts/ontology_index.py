#!/usr/bin/env python3
"""Build generated/index.json from ontology YAML files."""
from __future__ import annotations
import json, sys
from pathlib import Path
import yaml

CATEGORIES = ["objects","relations","states","rules","actions","policies","workflows","connectors","mappings","projections"]

def main(root_arg: str) -> int:
    root = Path(root_arg).resolve()
    index = {"ontology_root": str(root), "items": {}}
    for category in CATEGORIES:
        items = []
        folder = root / category
        if folder.exists():
            for p in sorted(folder.rglob("*.y*ml")):
                with p.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                items.append({
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "lifecycle": data.get("lifecycle"),
                    "path": str(p.relative_to(root)),
                })
        index["items"][category] = items
    out = root / "generated" / "index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ontology_index.py <ontology-root>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
