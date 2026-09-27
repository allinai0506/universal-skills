#!/usr/bin/env python3
"""Initialize semantic-domain-modeling artifacts without overwriting existing work.

Greenfield:
  docs/domain-model.md

Brownfield:
  docs/domain-model.md
  docs/semantic-conflicts.md
  docs/source-of-truth.md
  docs/semantic-migration-plan.md
"""

from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys


def copy_if_absent(source: Path, target: Path) -> str:
    if target.exists():
        return f"EXISTS: {target}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return f"CREATED: {target}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="Repository root")
    parser.add_argument(
        "--mode",
        choices=("greenfield", "brownfield"),
        default="greenfield",
        help="Initialization mode (default: greenfield)",
    )
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists() or not repo.is_dir():
        print(f"ERROR: repository directory does not exist: {repo}")
        return 2

    if args.mode == "greenfield":
        pairs = [
            (skill_root / "assets" / "domain-model.template.md", repo / "docs" / "domain-model.md"),
        ]
    else:
        pairs = [
            (skill_root / "assets" / "brownfield-domain-model.template.md", repo / "docs" / "domain-model.md"),
            (skill_root / "assets" / "semantic-conflicts.template.md", repo / "docs" / "semantic-conflicts.md"),
            (skill_root / "assets" / "source-of-truth.template.md", repo / "docs" / "source-of-truth.md"),
            (skill_root / "assets" / "semantic-migration-plan.template.md", repo / "docs" / "semantic-migration-plan.md"),
        ]

    created = 0
    for source, target in pairs:
        message = copy_if_absent(source, target)
        print(message)
        if message.startswith("CREATED:"):
            created += 1

    if created == 0:
        print("STOP: no files created; existing artifacts were preserved")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
