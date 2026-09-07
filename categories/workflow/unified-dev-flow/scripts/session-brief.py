#!/usr/bin/env python3
"""SessionStart memory brief — assemble (never invent) project memory.

Reads ONLY existing file-based stores (no model calls, no MCP, no network):
  1. ck project memory  (~/.claude/ck, $CK_HOME to override)
  2. project wiki       (<project>/.omc/wiki/index.md + log tail)
  3. ledger breakpoint  (<project>/.superpowers/sdd/progress.md)
  4. decision trail     (<project>/decisions.tsv freshness)
  5. gate stats         (entry-gate block log, last 7d for this project)

Prints a compact markdown brief to stdout (SessionStart hooks surface
stdout as context on all tools). Missing stores print 无 and are skipped.
ALWAYS exits 0 — a briefing must never block a session.
Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

CK_LINES = 60
WIKI_INDEX_LINES = 30
WIKI_LOG_TAIL = 5


def ck_home() -> str:
    return os.environ.get("CK_HOME", os.path.join(os.path.expanduser("~"), ".claude", "ck"))


def read_lines(path: str, limit: int) -> list[str] | None:
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return [line.rstrip("\n") for _, line in zip(range(limit), f)]
    except OSError:
        return None


def read_tail(path: str, n: int) -> list[str] | None:
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return [line.rstrip("\n") for line in f.readlines()[-n:]]
    except OSError:
        return None


def ck_section(project_dir: str) -> list[str]:
    """Match project by path in ck projects.json, print CONTEXT.md excerpt."""
    out = ["## 项目记忆（ck）"]
    try:
        with open(os.path.join(ck_home(), "projects.json"), encoding="utf-8") as f:
            projects = json.load(f)
    except (OSError, ValueError):
        return out + ["（无：ck store 不可读）"]
    match = ""
    if isinstance(projects, dict):
        for _key, info in projects.items():
            if not isinstance(info, dict):
                continue
            p = str(info.get("path", ""))
            name = str(info.get("name", _key))
            if p and (os.path.abspath(project_dir) == os.path.abspath(p)
                      or os.path.abspath(project_dir).startswith(os.path.abspath(p) + os.sep)):
                match = name
                break
    if not match:
        return out + ["（无：本项目未在 ck 注册）"]
    lines = read_lines(os.path.join(ck_home(), "contexts", match, "CONTEXT.md"), CK_LINES)
    if not lines:
        return out + [f"（无：{match} 的 CONTEXT.md 缺失）"]
    return out + [f"（{match}，前 {CK_LINES} 行）"] + lines


def wiki_section(project_dir: str) -> list[str]:
    out = ["## 项目 wiki"]
    idx = read_lines(os.path.join(project_dir, ".omc", "wiki", "index.md"), WIKI_INDEX_LINES)
    if not idx:
        return out + ["（无：.omc/wiki/index.md 缺失）"]
    out += ["（index）"] + idx
    tail = read_tail(os.path.join(project_dir, ".omc", "wiki", "log.md"), WIKI_LOG_TAIL)
    if tail:
        out += ["（最近沉淀）"] + tail
    return out


def ledger_section(project_dir: str) -> list[str]:
    out = ["## 断点续跑"]
    lines = read_lines(os.path.join(project_dir, ".superpowers", "sdd", "progress.md"), 200)
    if not lines:
        return out + ["（无未完成 ledger，走正常分级）"]
    head = next((line for line in lines if line.strip()), "（空）")
    done = sum(1 for line in lines if "complete" in line.lower())
    return out + [f"计划：{head}", f"已完成 Task 行：{done}（从下一行续跑，不重分级）"]


def trail_section(project_dir: str) -> list[str]:
    out = ["## 决策轨迹"]
    p = os.path.join(project_dir, "decisions.tsv")
    try:
        fresh = (os.path.isfile(p) and os.path.getsize(p) > 0
                 and datetime.date.fromtimestamp(os.path.getmtime(p))
                 == datetime.date.today())
    except OSError:
        fresh = False
    return out + (["decisions.tsv 当日新鲜 ✅"] if fresh else ["（无当日 decisions.tsv）"])


def blocks_section(project_dir: str) -> list[str]:
    out = ["## 门禁统计"]
    log = (os.environ.get("ENTRY_GATE_BLOCKLOG")
           or os.path.join(os.path.expanduser("~"), ".claude", "homunculus",
                           "entry-gate-blocks.jsonl"))
    try:
        since = datetime.datetime.now() - datetime.timedelta(days=7)
        n = 0
        kinds: dict[str, int] = {}
        with open(log, encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except (json.JSONDecodeError, TypeError):
                    continue
                if not isinstance(row, dict) or row.get("project") != project_dir:
                    continue
                try:
                    ts = datetime.datetime.fromisoformat(str(row.get("ts", "")))
                except ValueError:
                    continue
                if ts >= since:
                    n += 1
                    k = str(row.get("kind", "?"))
                    kinds[k] = kinds.get(k, 0) + 1
    except OSError:
        return out + ["（无 block 日志）"]
    if not n:
        return out + ["近7天拦截：0"]
    detail = " ".join(f"{k}x{v}" for k, v in sorted(kinds.items()))
    return out + [f"近7天拦截：{n}（{detail}）"]


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", default="")
    ns = ap.parse_args(argv)
    project_dir = ns.project_dir or os.getcwd()
    sections: list[str] = [f"# Session Brief — {project_dir}"]
    for fn in (ck_section, wiki_section, ledger_section, trail_section, blocks_section):
        try:
            sections += [""] + fn(project_dir)
        except OSError:
            sections += ["", "（该节读取失败，已跳过）"]
    sys.stdout.write("\n".join(sections) + "\n")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
    sys.exit(0)
