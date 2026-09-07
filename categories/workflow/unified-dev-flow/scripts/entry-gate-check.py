#!/usr/bin/env python3
"""Entry Gate enforcer for the unified-dev-flow router.

Mechanical (deterministic) counterpart of the SKILL.md "Entry Gate" section:
before the agent's first Edit/Write in a session, it must have written the
entry-gate artifact. No artifact (or a malformed one) -> BLOCK.

Artifact contract (see references/enforcement.md):
    <project>/.omc/entry-gate-<sessionID>.md
Must contain the 4 headers (理解和假设 / 最小方案 / 范围纪律 / 验证计划),
at least one list item under §2 (the file-scope list), and >= MIN_CHARS total.

Usage as a Claude Code PreToolUse hook (matcher Edit|Write):
    python3 entry-gate-check.py   # reads hook JSON from stdin
Manual / test usage:
    python3 entry-gate-check.py --project-dir <dir> --session-id <id>

Exit codes: 0 = pass, 2 = block (reason on stderr, which Claude surfaces).
Stdlib only. Honest limitation (same as delivery-gate): this checks that the
artifact EXISTS and is well-formed, not that its content is truthful.
Downstream gates (S5 evidence, S6 review) catch garbage content.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import datetime
from typing import NoReturn

SECTIONS = ("理解和假设", "最小方案", "范围纪律", "验证计划")
MIN_CHARS = 150
TRAIL_MIN_EDITS = 8  # fewer edits than this needs no decision trail
CODEGRAPH_TIMEOUT = 15

# tool_input keys that may carry the write target, across tools
# (Claude/Trae: file_path; OpenCode: filePath; Antigravity: TargetFile; ...)
TARGET_KEYS = ("file_path", "filePath", "path", "file", "filename",
               "target_file", "TargetFile")

PATH_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java",
             ".md", ".json", ".yaml", ".yml", ".toml", ".sh", ".sql",
             ".vue", ".css", ".html", ".c", ".h", ".cpp")


def fail(msg: str) -> NoReturn:
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(2)


def resolve_context(argv: list[str] | None = None) -> tuple[str, str, str]:
    """Return (project_dir, session_id, target).

    target = the file this tool call writes (for self-exemption), from
    --target, stdin tool_input path fields, or apply_patch command text.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--target", default="")
    ns, _ = ap.parse_known_args(argv)

    project_dir = ns.project_dir
    session_id = ns.session_id
    target = ns.target
    payload: dict = {}

    if not project_dir or not session_id or not target:
        try:
            raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        except OSError:
            raw = ""
        if raw.strip():
            try:
                parsed = json.loads(raw)
                payload = parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                payload = {}
        if not session_id:
            session_id = str(payload.get("session_id") or payload.get("sessionID") or "")
        if not project_dir:
            project_dir = str(payload.get("cwd") or payload.get("project_dir") or "")
        if not target:
            tool_input = payload.get("tool_input")
            if isinstance(tool_input, dict):
                for key in TARGET_KEYS:
                    val = tool_input.get(key)
                    if isinstance(val, str) and val.strip():
                        target = val.strip()
                        break
                if not target:
                    cmd = tool_input.get("command")
                    if isinstance(cmd, str):
                        # Codex apply_patch shape: "*** Update File: <path>"
                        m = re.search(r"^\*\*\* (?:Update|Add) File:\s*(\S+)",
                                      cmd, re.MULTILINE)
                        if m:
                            target = m.group(1).strip()

    if not project_dir:
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    if not session_id:
        session_id = "default"
    # Keep the filename safe: session ids are usually alnum/- already.
    session_id = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)
    return project_dir, session_id, target


def is_artifact_target(project_dir: str, target: str) -> bool:
    """True if the write targets an entry-gate artifact itself.

    Writing the artifact is always gate-compliant (it IS the compliance
    action); content is validated on subsequent edits. Without this,
    the first task deadlocks: no artifact without a write, no write
    without an artifact.
    """
    if not target:
        return False
    abs_target = os.path.abspath(
        target if os.path.isabs(target) else os.path.join(project_dir, target))
    abs_proj = os.path.abspath(project_dir)
    try:
        same_root = os.path.commonpath([abs_proj, abs_target]) == abs_proj
    except ValueError:
        return False
    if not same_root:
        return False
    parent, base = os.path.split(abs_target)
    return (os.path.basename(parent) == ".omc"
            and base.startswith("entry-gate-") and base.endswith(".md"))


def artifact_path(project_dir: str, session_id: str) -> str:
    return os.path.join(project_dir, ".omc", f"entry-gate-{session_id}.md")


def scope_marker_path(project_dir: str, session_id: str) -> str:
    return os.path.join(project_dir, ".omc", f".scope-ok-{session_id}")


def extract_scope_paths(content: str) -> list[tuple[bool, str]]:
    """Pull (is_new, path) pairs from §2's file-scope list.

    Convention: brand-new files are prefixed `NEW:` and skip existence
    checks; everything else must exist (or be known to the codegraph index).
    """
    m2 = re.search(r"^##\s*.*最小方案", content, re.MULTILINE)
    m3 = re.search(r"^##\s*.*范围纪律", content, re.MULTILINE)
    section2 = content[m2.start(): m3.start() if m3 else len(content)] if m2 else ""
    found: list[tuple[bool, str]] = []
    for line in section2.splitlines():
        m = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$", line)
        if not m:
            continue
        item = m.group(1).strip()
        is_new = item.upper().startswith("NEW:")
        if is_new:
            item = item[4:].strip()
        for token in re.split(r"\s+", item):
            token = token.strip("`'\"(),;:.!?[]{}")
            if not token or token.startswith(("-", "http", "<", "$")):
                continue
            if "/" in token or token.lower().endswith(PATH_EXTS):
                # strip trailing parentheticals like "(new)" leftovers
                token = re.sub(r"\(.*\)$", "", token)
                if token:
                    found.append((is_new, token))
    return dedupe_keep_order(found)


def dedupe_keep_order(pairs: list[tuple[bool, str]]) -> list[tuple[bool, str]]:
    seen: set[str] = set()
    out: list[tuple[bool, str]] = []
    for is_new, path in pairs:
        if path not in seen:
            seen.add(path)
            out.append((is_new, path))
    return out


def codegraph_has_symbol(project_dir: str, name: str) -> bool | None:
    """True/False via `codegraph query`; None when unverifiable (no index/CLI/error)."""
    if not os.path.isdir(os.path.join(project_dir, ".codegraph")):
        return None
    exe = shutil.which("codegraph")
    if not exe:
        return None
    stem = os.path.splitext(os.path.basename(name))[0]
    if not stem:
        return None
    try:
        proc = subprocess.run(
            [exe, "query", "-p", project_dir, "-j", stem],
            capture_output=True, text=True, timeout=CODEGRAPH_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    try:
        data = json.loads(proc.stdout)
    except (json.JSONDecodeError, TypeError):
        return None
    return bool(data) if isinstance(data, list) else None


def verify_scope(project_dir: str, content: str) -> str | None:
    """Return None if the §2 file list checks out, else the blocking reason."""
    problems: list[str] = []
    abs_proj = os.path.abspath(project_dir)
    has_index = os.path.isdir(os.path.join(project_dir, ".codegraph"))
    cli_ok = shutil.which("codegraph") is not None
    for is_new, path in extract_scope_paths(content):
        if is_new:
            continue
        abs_target = os.path.abspath(
            path if os.path.isabs(path) else os.path.join(project_dir, path))
        try:
            inside = os.path.commonpath([abs_proj, abs_target]) == abs_proj
        except ValueError:
            inside = False
        if not inside:
            problems.append(f"{path}（超出项目目录）")
            continue
        if os.path.exists(abs_target):
            continue
        if has_index and cli_ok:
            symbol = codegraph_has_symbol(project_dir, path)
            if symbol is True:
                continue
            if symbol is None:
                # Broken CLI with an index present: fail OPEN (env issue,
                # never deadlock the session), warn loudly.
                sys.stderr.write(f"WARN: codegraph 查询失败，跳过索引校验：{path}\n")
                continue
            problems.append(f"{path}（磁盘与索引中都不存在；新建请标 NEW:）")
        else:
            problems.append(f"{path}（不存在；新建文件请标 NEW:，否则检查 typo）")
        if len(problems) >= 3:
            problems.append("…（仅显示前 3 个）")
            break
    if not problems:
        return None
    return ("文件范围清单未通过校验：" + "；".join(problems)
            + "。修正清单后重试刚才的工具调用。")


TEMPLATE_HINT = (
    "Entry Gate 缺失或不合格，STOP。先写入口产物再动手：\n"
    "  <project>/.omc/entry-gate-<sessionID>.md，须含 4 节标题 "
    "(## 1. 理解和假设 / ## 2. 最小方案 / ## 3. 范围纪律 / ## 4. 验证计划)，"
    "§2 须有用 - 或 1. 开头的条目列出文件范围，全文 >= 150 字。"
    "不许重述规则（如'我将遵循 TDD'），只许写实例"
    "（如'失败测试：tests/x_test.py::test_y；验证命令：pytest tests/x_test.py'）。"
    "写完后重试刚才的工具调用。"
)


def validate(content: str) -> str | None:
    """Return None if valid, else the blocking reason."""
    for keyword in SECTIONS:
        if not re.search(rf"^##\s*.*{keyword}", content, re.MULTILINE):
            return f"缺少章节：{keyword}。"
    # §2 (最小方案) must carry the file-scope list: at least one list item
    # between the §2 header and the §3 header.
    m2 = re.search(r"^##\s*.*最小方案", content, re.MULTILINE)
    m3 = re.search(r"^##\s*.*范围纪律", content, re.MULTILINE)
    section2 = content[m2.start(): m3.start() if m3 else len(content)] if m2 else ""
    if not re.search(r"^\s*(?:[-*]|\d+[.)])\s+\S", section2, re.MULTILINE):
        return "§2 最小方案缺少文件范围条目（用 - 或 1. 列出要改的文件）。"
    if len(content) < MIN_CHARS:
        return f"全文过短（{len(content)} < {MIN_CHARS} 字），每节写 1–2 句实在话。"
    return None


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-trail", action="store_true")
    ap.add_argument("--transcript", default="")
    ap.add_argument("--trail", default="")
    ap.add_argument("--min-edits", type=int, default=TRAIL_MIN_EDITS)
    ap.add_argument("--project-dir", default="")
    ap.add_argument("--session-id", default="")
    early, _ = ap.parse_known_args(argv)
    if early.check_trail:
        cmd_check_trail(early)
        return
    project_dir, session_id, target = resolve_context(argv)
    if target and is_artifact_target(project_dir, target):
        sys.exit(0)  # writing the artifact itself is always allowed
    path = artifact_path(project_dir, session_id)
    if not os.path.isfile(path):
        fail(TEMPLATE_HINT + f"\n当前缺失：{path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        fail(f"入口产物不可读：{path}（{e}）。")
    reason = validate(content)
    if reason is not None:
        fail("入口产物不合格：" + reason + "\n" + TEMPLATE_HINT)
    run_scope_check(project_dir, session_id, path, content)
    sys.exit(0)


def run_scope_check(project_dir: str, session_id: str,
                    artifact: str, content: str) -> None:
    """First-gated-edit scope validation, cached per session.

    Skipped when the marker is newer than the artifact (plan unchanged).
    Re-runs whenever the artifact is edited — a changed plan re-validates.
    """
    marker = scope_marker_path(project_dir, session_id)
    try:
        fresh = (os.path.isfile(marker)
                 and os.path.getmtime(marker) >= os.path.getmtime(artifact))
    except OSError:
        fresh = False
    if fresh:
        return
    reason = verify_scope(project_dir, content)
    if reason is not None:
        fail(reason)
    try:
        with open(marker, "w", encoding="utf-8") as f:
            f.write("scope ok\n")
    except OSError:
        pass  # marker is an optimization; a failed write must not block


def read_transcript_text(transcript_arg: str) -> str:
    if transcript_arg and os.path.isfile(transcript_arg):
        try:
            with open(transcript_arg, "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    except OSError:
        return ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, TypeError):
        return ""
    if isinstance(payload, dict) and payload.get("transcript_path"):
        tp = os.path.expanduser(str(payload["transcript_path"]))
        if os.path.isfile(tp):
            try:
                with open(tp, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                pass
    return raw if isinstance(raw, str) else ""


def cmd_check_trail(ns: argparse.Namespace) -> None:
    """Stop-hook mode: complex work must leave a decision trail.

    Small work (< --min-edits Edit/Write calls) passes without one.
    Trail = <project>/decisions.tsv (show-me-your-work default), must exist,
    be non-empty, and be touched today. Exit 2 blocks the stop.
    """
    project_dir = ns.project_dir or ""
    if not project_dir:
        try:
            raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        except OSError:
            raw = ""
        project_dir = ""
        try:
            payload = json.loads(raw) if raw.strip() else {}
            if isinstance(payload, dict):
                project_dir = str(payload.get("cwd") or payload.get("project_dir") or "")
        except (json.JSONDecodeError, TypeError):
            pass
        if not project_dir:
            project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    # NOTE: resolve_context() is writer-gate shaped (needs session/target);
    # trail mode re-derives project_dir here to avoid consuming stdin twice.
    transcript = read_transcript_text(ns.transcript)
    edits = len(re.findall(r'"name":\s*"(?:Edit|Write)"', transcript))
    if edits < ns.min_edits:
        sys.exit(0)
    trail = ns.trail or os.path.join(project_dir, "decisions.tsv")
    ok = False
    try:
        ok = (os.path.isfile(trail) and os.path.getsize(trail) > 0
              and datetime.date.fromtimestamp(os.path.getmtime(trail))
              == datetime.date.today())
    except OSError:
        ok = False
    if not ok:
        fail(f"复杂工作（{edits} 次写操作）缺少当日决策轨迹：{trail}。"
             "按 show-me-your-work 写 decisions.tsv 后再结束。")
    sys.exit(0)


if __name__ == "__main__":
    main()
