#!/usr/bin/env python3
"""Summarize git changes under an ontology directory and flag likely breaking changes.

Usage: python scripts/ontology_diff.py <base-ref> <head-ref> [ontology-path]
"""
from __future__ import annotations
import subprocess, sys

BREAKING_HINTS = [
    "deleted file mode",
    "-cardinality:",
    "-  - from:",
    "-allowed_actions:",
    "-effects:",
    "-id:",
]

def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)

def main(base: str, head: str, path: str) -> int:
    names = run("git", "diff", "--name-status", base, head, "--", path)
    patch = run("git", "diff", "--unified=1", base, head, "--", path)
    print("Changed ontology files:")
    print(names.strip() or "(none)")
    breaking = [h for h in BREAKING_HINTS if h in patch]
    print("\nBreaking-change heuristic:")
    if breaking:
        print("REVIEW_REQUIRED")
        for h in breaking:
            print(f"  matched: {h}")
        return 3
    print("No obvious breaking-change pattern detected. Human review is still required for Action/Policy semantics.")
    return 0

if __name__ == "__main__":
    if len(sys.argv) not in (3,4):
        print("Usage: ontology_diff.py <base-ref> <head-ref> [ontology-path]")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)==4 else "ontology"))
