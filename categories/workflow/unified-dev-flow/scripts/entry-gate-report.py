#!/usr/bin/env python3
"""Weekly value report for the Entry Gate.

Reads the JSONL block log (see entry-gate-check.py log_block) and prints:
  total blocks, counts by kind, by project, by day — plus a "dead gate" hint
  (kinds with zero blocks in the window may be ceremony, not enforcement).

Usage:
  python3 entry-gate-report.py [--log PATH] [--days N]
  Defaults: log=~/.claude/homunculus/entry-gate-blocks.jsonl (or
  $ENTRY_GATE_BLOCKLOG), days=7.

Stdlib only. Exit 0 always (reporting never blocks anything).
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import sys

TAIL_LINES = 20000  # reports aggregate recent history; never load it all

DEFAULT_LOG = os.environ.get(
    "ENTRY_GATE_BLOCKLOG",
    os.path.join(os.path.expanduser("~"), ".claude", "homunculus",
                 "entry-gate-blocks.jsonl"))

KINDS = ("missing", "malformed", "scope", "trail")


def load_rows(path: str, since: datetime.datetime) -> list[dict]:
    rows: list[dict] = []
    try:
        with open(path, encoding="utf-8") as f:
            tail = collections.deque(f, maxlen=TAIL_LINES)
    except OSError:
        return rows
    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        try:
            ts = datetime.datetime.fromisoformat(str(row.get("ts", "")))
        except ValueError:
            continue
        if ts >= since and isinstance(row, dict):
            rows.append(row)
    return rows


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--days", type=int, default=7)
    ns = ap.parse_args(argv)
    since = datetime.datetime.now() - datetime.timedelta(days=max(ns.days, 1))
    rows = load_rows(ns.log, since)

    by_kind: collections.Counter[str] = collections.Counter()
    by_proj: collections.Counter[str] = collections.Counter()
    by_day: collections.Counter[str] = collections.Counter()
    for r in rows:
        by_kind[str(r.get("kind", "?"))] += 1
        by_proj[str(r.get("project", "?"))] += 1
        by_day[str(r.get("ts", "?"))[:10]] += 1

    print(f"entry-gate report (last {ns.days}d, {ns.log})")
    print(f"total: {len(rows)}")
    for k in list(KINDS) + sorted(set(by_kind) - set(KINDS)):
        print(f"{k}: {by_kind.get(k, 0)}")
    dead = [k for k in KINDS if by_kind.get(k, 0) == 0]
    if rows and dead:
        print(f"dead-gate hint (0 blocks, maybe ceremony): {', '.join(dead)}")
    if not rows:
        print("no blocks in window (gates quiet or not yet installed)")
        return
    print("by-project:")
    for proj, n in by_proj.most_common(5):
        print(f"  {n}x {proj}")
    print("by-day:")
    for day in sorted(by_day):
        print(f"  {day}: {by_day[day]}")


if __name__ == "__main__":
    main()
