#!/usr/bin/env python3
"""Regression tests for repository-specific skill frontmatter metadata."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("quick_validate", SCRIPT_DIR / "quick_validate.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_skill(frontmatter: str) -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n# Test\n", encoding="utf-8")
    return root


def main() -> int:
    standard = write_skill("name: demo\ndescription: Demo skill")
    repository = write_skill(
        'name: demo\nversion: "2026.09.10-2"\n'
        'synced-at: "2026-09-10T19:33:57"\ndescription: Demo skill'
    )
    unknown = write_skill("name: demo\ndescription: Demo skill\nmade-up-key: true")

    assert MODULE.validate_skill(standard)[0]
    assert MODULE.validate_skill(repository)[0]
    ok, message = MODULE.validate_skill(unknown)
    assert not ok and "made-up-key" in message
    print("All quick validator tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
