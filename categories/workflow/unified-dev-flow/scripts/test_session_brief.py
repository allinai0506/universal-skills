#!/usr/bin/env python3
"""Tests for session-brief.py (SessionStart memory brief, file-based only).

Builds a fixture project (ck store + wiki + ledger + trail + block log),
asserts the brief contains each section, and asserts graceful degradation.
Stdlib only:  python3 test_session_brief.py

TDD: written BEFORE session-brief.py existed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session-brief.py")
FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def build_fixture() -> tuple[str, str, dict[str, str]]:
    proj = tempfile.mkdtemp()
    ckhome = tempfile.mkdtemp()
    # ck store
    with open(os.path.join(ckhome, "projects.json"), "w") as f:
        json.dump({"demo": {"path": proj, "name": "demo"}}, f)
    ctxd = os.path.join(ckhome, "contexts", "demo")
    os.makedirs(ctxd)
    with open(os.path.join(ctxd, "CONTEXT.md"), "w") as f:
        f.write("# demo context\nGoal: ship the thing.\nConstraints: no mocks.\n" + "x\n" * 80)
    # wiki
    wikid = os.path.join(proj, ".omc", "wiki")
    os.makedirs(wikid)
    with open(os.path.join(wikid, "index.md"), "w") as f:
        f.write("# index\n- auth.md\n")
    with open(os.path.join(wikid, "log.md"), "w") as f:
        f.write("2026-09-01 ingested auth\n2026-09-02 fixed login\n")
    # ledger
    sdd = os.path.join(proj, ".superpowers", "sdd")
    os.makedirs(sdd)
    with open(os.path.join(sdd, "progress.md"), "w") as f:
        f.write("# Plan: specs/auth/plan.md\nTask 3: complete\nTask 4: pending\n")
    # trail
    with open(os.path.join(proj, "decisions.tsv"), "w") as f:
        f.write("date\tdecision\twhy\tevidence\tresult\n2026-09-07\tused X\tY\tf.py\tok\n")
    os.utime(os.path.join(proj, "decisions.tsv"), None)
    # block log
    blog = os.path.join(proj, "blocks.jsonl")
    with open(blog, "w") as f:
        f.write('{"ts": "2026-09-07T10:00:00", "kind": "missing", "session": "s", "project": "%s", "reason": "r"}\n' % proj)
    env = {"CK_HOME": ckhome, "ENTRY_GATE_BLOCKLOG": blog, "PATH": os.environ.get("PATH", "")}
    return proj, ckhome, env


def run(proj: str, env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, SCRIPT, "--project-dir", proj],
        capture_output=True, text=True, timeout=30,
        env={**os.environ, **env})


def main() -> None:
    check("script-exists", os.path.isfile(SCRIPT), "session-brief.py missing (RED?)")
    if not os.path.isfile(SCRIPT):
        print("\n1 failure(s).")
        sys.exit(1)
    proj, ckhome, env = build_fixture()
    r = run(proj, env)
    out = r.stdout
    check("exit-zero-always", r.returncode == 0, f"exit={r.returncode} stderr={r.stderr[:200]}")
    check("brief-ck", "ship the thing" in out, "CONTEXT.md excerpt missing")
    check("brief-wiki", "auth.md" in out and "fixed login" in out, "wiki section missing")
    check("brief-ledger", "specs/auth/plan.md" in out and "已完成 Task 行：1" in out, "ledger section missing")
    check("brief-trail", "decisions.tsv" in out, "trail section missing")
    check("brief-blocks", "近7天拦截" in out, "block stats missing")

    # graceful degradation: empty project briefs without crashing
    with tempfile.TemporaryDirectory() as bare:
        r2 = subprocess.run(
            [sys.executable, SCRIPT, "--project-dir", bare],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "CK_HOME": os.path.join(bare, "nock"),
                 "ENTRY_GATE_BLOCKLOG": os.path.join(bare, "noblog")})
        check("bare-project-zero", r2.returncode == 0, f"exit={r2.returncode}")
        check("bare-project-marks-absent", "无" in r2.stdout, "missing stores not marked")

    # oversized block log: tail cap keeps counts exact, never loads it all
    biglog = os.path.join(proj, "big.jsonl")
    with open(biglog, "w") as f:
        for _ in range(100):
            f.write('{"ts": "2020-01-01T00:00:00", "kind": "missing", "session": "o", "project": "%s", "reason": "old"}\n' % proj)
        for _ in range(5):
            f.write('{"ts": "2026-09-07T10:00:00", "kind": "scope", "session": "n", "project": "%s", "reason": "new"}\n' % proj)
    env["ENTRY_GATE_BLOCKLOG"] = biglog
    r3 = run(proj, env)
    check("biglog-counts-exact", "近7天拦截：5（scopex5）" in r3.stdout,
          r3.stdout[-200:])

    import shutil
    shutil.rmtree(proj, ignore_errors=True)
    shutil.rmtree(ckhome, ignore_errors=True)
    print(f"\n{len(FAILURES)} failure(s)." if FAILURES else "\nAll tests passed.")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
