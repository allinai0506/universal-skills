#!/usr/bin/env python3
"""Bootstrap a minimal ontology/ directory in a target repository.

Usage: python ontology_bootstrap.py <repo-root> [name]
"""
from __future__ import annotations
import sys
from pathlib import Path

DIRS = [
    "objects", "relations", "states", "rules", "actions", "policies",
    "workflows", "connectors", "mappings", "projections", "tests/golden",
    "decisions", "proposals", "generated"
]

MANIFEST = """version: 0.1.0
name: {name}
description: \"Repository ontology\"
default_language: zh-CN
lifecycle_values:
  - experimental
  - active
  - deprecated
"""

GITKEEP_DIRS = ["objects", "relations", "states", "rules", "actions", "policies", "workflows", "connectors", "mappings", "projections", "tests/golden", "decisions", "proposals"]


def main(repo_arg: str, name: str) -> int:
    repo = Path(repo_arg).resolve()
    ont = repo / "ontology"
    ont.mkdir(parents=True, exist_ok=True)
    for d in DIRS:
        (ont / d).mkdir(parents=True, exist_ok=True)
    manifest = ont / "ontology.yaml"
    if not manifest.exists():
        manifest.write_text(MANIFEST.format(name=name), encoding="utf-8")
    for d in GITKEEP_DIRS:
        p = ont / d / ".gitkeep"
        if not any((ont / d).iterdir()):
            p.touch()
    print(f"Bootstrapped: {ont}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) not in (2,3):
        print("Usage: ontology_bootstrap.py <repo-root> [name]")
        raise SystemExit(2)
    root = Path(sys.argv[1]).resolve()
    default_name = root.name or "enterprise-ontology"
    raise SystemExit(main(sys.argv[1], sys.argv[2] if len(sys.argv)==3 else default_name))
