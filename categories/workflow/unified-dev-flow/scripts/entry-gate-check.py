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
Usage as a Stop hook (S6 teeth: every S6 must declare itself):
    python3 entry-gate-check.py --check-review   # needs .omc/verify-*.md + review-*.md
Manual / test usage:
    python3 entry-gate-check.py --project-dir <dir> --session-id <id>

Exit codes: 0 = pass, 2 = block (reason on stderr, which Claude surfaces).
Stdlib only. Honest limitation (same as delivery-gate): this checks that the
artifact EXISTS and is well-formed, not that its content is truthful.
Downstream gates (S5 evidence, S6 review) catch garbage content.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
from typing import NoReturn

SECTIONS = ("理解和假设", "最小方案", "范围纪律", "验证计划")
MIN_CHARS = 150
TRAIL_MIN_EDITS = 8  # fewer edits than this needs no decision trail
TRAIL_MAX_BLOCKS = 3  # then give up loudly instead of spinning forever
REVIEW_MIN_EDITS = 1  # any source edit means S4 ran, so S5/S6 artifacts are owed
REVIEW_MIN_CHARS = 80  # review artifacts are declarations, not essays
REVIEW_MAX_BLOCKS = 3  # same anti-spin ceiling as the trail check
REVIEW_VERDICTS = ("MERGE_READY", "NEEDS_FIXES", "ESCALATE")
CODEGRAPH_TIMEOUT = 5  # per-query ceiling; SCOPE_DEADLINE_S caps the total
SCOPE_DEADLINE_S = 6.0  # scope validation must never stall the hook itself
DEFAULT_BLOCKLOG = os.path.join(os.path.expanduser("~"), ".claude",
                                "homunculus", "entry-gate-blocks.jsonl")
_block_log_override = ""  # set by --block-log; never via os.environ mutation

# tool_input keys that may carry the write target, across tools
# (Claude/Trae: file_path; OpenCode: filePath; Antigravity: TargetFile; ...)
TARGET_KEYS = ("file_path", "filePath", "path", "file", "filename",
               "target_file", "TargetFile")

# Write-tool names across harnesses, for transcript edit counting.
# Claude/Codex/Cursor/Trae/Qoder/Kimi: Edit|Write; Gemini: write_file|replace;
# Antigravity: write_to_file|replace_file_content|multi_replace_file_content.
# Shape matched is always JSON ("name":"<tool>"), never prose.
EDIT_TOOL_PATTERN = (r'"name":\s*"(?:Edit|Write|write_file|replace|'
                     r'write_to_file|replace_file_content|'
                     r'multi_replace_file_content)"')

PATH_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java",
             ".md", ".json", ".yaml", ".yml", ".toml", ".sh", ".sql",
             ".vue", ".css", ".html", ".c", ".h", ".cpp")


def blocklog_path() -> str:
    return (_block_log_override
            or os.environ.get("ENTRY_GATE_BLOCKLOG")
            or DEFAULT_BLOCKLOG)


def log_block(kind: str, session: str, project: str, reason: str) -> None:
    """Append one JSONL row per block. Logging must never block the gate."""
    try:
        path = blocklog_path()
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "kind": kind,
                "session": session,
                "project": project,
                "reason": reason[:160],
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass


def fail(msg: str, kind: str = "block", session: str = "",
         project: str = "") -> NoReturn:
    text = msg.rstrip()
    sys.stderr.write(text + "\n")
    log_block(kind, session, project, text.splitlines()[0] if text else "")
    sys.exit(2)


def read_stdin_text() -> str:
    try:
        return sys.stdin.read() if not sys.stdin.isatty() else ""
    except OSError:
        return ""


def parse_stdin_json(raw: str) -> dict:
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def resolve_context(argv: list[str] | None = None,
                    raw: str | None = None) -> tuple[str, str, str]:
    """Return (project_dir, session_id, target).

    target = the file this tool call writes (for self-exemption), from
    --target, stdin tool_input path fields, or apply_patch command text.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--target", default="")
    ap.add_argument("--block-log", default="")
    ns, _ = ap.parse_known_args(argv)
    if ns.block_log:
        global _block_log_override
        _block_log_override = ns.block_log

    project_dir = ns.project_dir
    session_id = ns.session_id
    target = ns.target
    if raw is None:
        raw = read_stdin_text()
    payload: dict = {}

    if not project_dir or not session_id or not target:
        payload = parse_stdin_json(raw)
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


def _is_within(abs_proj: str, abs_target: str) -> bool:
    """True if abs_target lives under abs_proj (both must be absolute)."""
    try:
        return os.path.commonpath([abs_proj, abs_target]) == abs_proj
    except ValueError:
        return False


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
    if not _is_within(abs_proj, abs_target):
        return False
    parent, base = os.path.split(abs_target)
    return (os.path.basename(parent) == ".omc"
            and base.startswith("entry-gate-") and base.endswith(".md"))


def artifact_path(project_dir: str, session_id: str) -> str:
    return os.path.join(project_dir, ".omc", f"entry-gate-{session_id}.md")


def scope_marker_path(project_dir: str, session_id: str) -> str:
    return os.path.join(project_dir, ".omc", f".scope-ok-{session_id}")


def verify_artifact_path(project_dir: str, session_id: str) -> str:
    return os.path.join(project_dir, ".omc", f"verify-{session_id}.md")


def review_artifact_path(project_dir: str, session_id: str) -> str:
    return os.path.join(project_dir, ".omc", f"review-{session_id}.md")


def review_counter_path(project_dir: str, session_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "default")
    return os.path.join(project_dir, ".omc", f".review-blocks-{safe}")


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
    deadline = time.monotonic() + SCOPE_DEADLINE_S
    for is_new, path in extract_scope_paths(content):
        if is_new:
            continue
        abs_target = os.path.abspath(
            path if os.path.isabs(path) else os.path.join(project_dir, path))
        inside = _is_within(abs_proj, abs_target)
        if not inside:
            problems.append(f"{path}（超出项目目录）")
            continue
        if os.path.exists(abs_target):
            continue
        if has_index and cli_ok:
            if time.monotonic() > deadline:
                sys.stderr.write(
                    f"WARN: scope 校验超时（>{SCOPE_DEADLINE_S:g}s），跳过剩余索引查询：{path}\n")
                continue
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
    "§2 须有用 - 或 1. 开头的条目列出文件范围（新建文件标 NEW: 前缀），全文 >= 150 字。"
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


EDIT_TOOL_NAMES = {"Edit", "Write", "write_file", "replace",
                   "write_to_file", "replace_file_content",
                   "multi_replace_file_content"}


def _tool_use_blocks(obj: object):
    """Yield (name, input_dict) for every toolUse/tool_use block in obj."""
    if isinstance(obj, dict):
        t = obj.get("type") or obj.get("kind")
        if t in ("toolUse", "tool_use", "function_call"):
            name = obj.get("name") or ""
            inp = obj.get("input") or obj.get("arguments") or {}
            yield name, inp if isinstance(inp, dict) else {}
        for value in obj.values():
            yield from _tool_use_blocks(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _tool_use_blocks(item)


def _is_omc_write(name: str, inp: dict) -> bool:
    """True for writes targeting the session's own .omc/ control files.

    Artifact writes (entry-gate/verify/review) are compliance actions, not
    S4 implementation edits; counting them would force a review on sessions
    that never touched source.
    """
    if name not in EDIT_TOOL_NAMES:
        return False
    for key in TARGET_KEYS:
        val = inp.get(key)
        if isinstance(val, str) and ".omc" in val.replace("\\", "/").split("/"):
            return True
    cmd = inp.get("command")
    if isinstance(cmd, str) and ".omc/" in cmd:
        return True
    return False


def count_source_edits(transcript: str) -> int:
    """Edits to real source, excluding .omc/ artifact writes.

    Parses transcript JSONL for toolUse blocks; falls back to the raw
    regex count when no parseable tool call is found (conservative:
    an unreadable transcript must not silently waive the gate).
    """
    parsed_any = False
    source = 0
    for line in transcript.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        blocks = list(_tool_use_blocks(obj))
        if not blocks:
            continue
        parsed_any = True
        for name, inp in blocks:
            if name in EDIT_TOOL_NAMES and not _is_omc_write(name, inp):
                source += 1
    if parsed_any:
        return source
    return len(re.findall(EDIT_TOOL_PATTERN, transcript))


def entry_gate_declares_patch(project_dir: str, session_id: str) -> bool:
    """True when the entry gate pins delivery_target to patch.

    A patch route is read-only by policy (no S4, hence no S6); the review
    check must not fire on it.
    """
    try:
        with open(artifact_path(project_dir, session_id), "r",
                  encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return False
    m1 = re.search(r"^##\s*.*理解和假设", content, re.MULTILINE)
    m2 = re.search(r"^##\s*.*最小方案", content, re.MULTILINE)
    section1 = content[m1.start(): m2.start() if m2 else len(content)] if m1 else content
    return re.search(r"delivery_target\s*[：:＝=]\s*patch",
                     section1, re.IGNORECASE) is not None


def validate_verify(content: str) -> str | None:
    """S5 evidence declaration: heading + command list + S4 cleanup record + minimum substance."""
    if not re.search(r"^##\s*.*验证证据", content, re.MULTILINE):
        return "缺少章节：验证证据（## 验证证据）。"
    if not re.search(r"^\s*(?:[-*]|\d+[.)])\s+\S", content, re.MULTILINE):
        return "验证证据缺少条目（用 - 或 1. 列出跑过的命令与 exit code）。"
    if not re.search(r"(?:ai-slop-cleaner|slop[- ]clean|瘦身|清理|deletion-first)", content, re.IGNORECASE):
        return "缺少 S4 收尾清理证据：必须记录 /ai-slop-cleaner 模式 B（deletion-first 瘦身/删死代码/化简结构）执行记录。"
    if len(content) < REVIEW_MIN_CHARS:
        return f"验证证据过短（{len(content)} < {REVIEW_MIN_CHARS} 字）。"
    return None


def validate_review(content: str) -> str | None:
    """S6 arrival declaration: heading + verdict + reviewer + round + google-code-review."""
    if not re.search(r"^##\s*.*评审结论", content, re.MULTILINE):
        return "缺少章节：评审结论（## 评审结论）。"
    if not re.search(r"\b(MERGE_READY|NEEDS_FIXES|ESCALATE)\b", content):
        return "评审结论缺少 verdict（MERGE_READY / NEEDS_FIXES / ESCALATE）。"
    if not re.search(r"reviewer\s*[：:]", content, re.IGNORECASE):
        return "评审结论缺少 reviewer: 行（注明模型/人，micro 可写 self）。"
    m = re.search(r"round\s*[：:]\s*(\d+)", content, re.IGNORECASE)
    if not m or int(m.group(1)) < 1:
        return "评审结论缺少 round: N 行（N ≥ 1，本轮评审计数）。"
    if not re.search(r"google-code-review", content, re.IGNORECASE):
        return "缺少 google-code-review 审查记录：S6 评审必须包含 /google-code-review 审查结论。"
    if len(content) < REVIEW_MIN_CHARS:
        return f"评审结论过短（{len(content)} < {REVIEW_MIN_CHARS} 字）。"
    return None


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-trail", action="store_true")
    ap.add_argument("--check-review", action="store_true")
    ap.add_argument("--transcript", default="")
    ap.add_argument("--trail", default="")
    ap.add_argument("--min-edits", type=int, default=TRAIL_MIN_EDITS)
    ap.add_argument("--max-blocks", type=int, default=TRAIL_MAX_BLOCKS)
    ap.add_argument("--project-dir", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--block-log", default="")
    early, _ = ap.parse_known_args(argv)
    if early.block_log:
        global _block_log_override
        _block_log_override = early.block_log
    if early.check_trail:
        cmd_check_trail(early)
        return
    if early.check_review:
        cmd_check_review(early)
        return
    project_dir, session_id, target = resolve_context(argv)
    if target and is_artifact_target(project_dir, target):
        sys.exit(0)  # writing the artifact itself is always allowed
    path = artifact_path(project_dir, session_id)
    if not os.path.isfile(path):
        fail(TEMPLATE_HINT + f"\n当前缺失：{path}",
             kind="missing", session=session_id, project=project_dir)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        fail(f"入口产物不可读：{path}（{e}）。",
             kind="malformed", session=session_id, project=project_dir)
    reason = validate(content)
    if reason is not None:
        fail("入口产物不合格：" + reason + "\n" + TEMPLATE_HINT,
             kind="malformed", session=session_id, project=project_dir)
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
        fail(reason, kind="scope", session=session_id, project=project_dir)
    try:
        with open(marker, "w", encoding="utf-8") as f:
            f.write("scope ok\n")
    except OSError:
        pass  # marker is an optimization; a failed write must not block


def read_transcript_text(transcript_arg: str, raw: str = "") -> str:
    if transcript_arg and os.path.isfile(transcript_arg):
        try:
            with open(transcript_arg, "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""
    payload = parse_stdin_json(raw)
    if payload.get("transcript_path"):
        tp = os.path.expanduser(str(payload["transcript_path"]))
        if os.path.isfile(tp):
            try:
                with open(tp, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                pass
    return raw if isinstance(raw, str) else ""


def trail_counter_path(project_dir: str, session_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "default")
    return os.path.join(project_dir, ".omc", f".trail-blocks-{safe}")


def read_trail_counter(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as f:
            return max(int(f.read().strip() or 0), 0)
    except (OSError, ValueError):
        return 0


def reset_trail_counter(path: str) -> None:
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


def cmd_check_trail(ns: argparse.Namespace) -> None:
    """Stop-hook mode: complex work must leave a decision trail.

    Small work (< --min-edits Edit/Write calls) passes without one.
    Trail = <project>/decisions.tsv (show-me-your-work default), must exist,
    be non-empty, and be touched today. Exit 2 blocks the stop — but at most
    --max-blocks times per episode, then it gives up loudly (a gate that
    spins the agent forever is worse than a missing trail).
    """
    project_dir = ns.project_dir or ""
    raw = ""
    if not project_dir or not ns.transcript or not ns.session_id:
        raw = read_stdin_text()
    session_id = ns.session_id or ""
    payload = parse_stdin_json(raw)
    if not session_id:
        session_id = str(payload.get("session_id") or payload.get("sessionID") or "")
    if not project_dir:
        project_dir = str(payload.get("cwd") or payload.get("project_dir") or "")
        if not project_dir:
            project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    counter = trail_counter_path(project_dir, session_id)
    transcript = read_transcript_text(ns.transcript, raw)
    edits = len(re.findall(EDIT_TOOL_PATTERN, transcript))
    if edits < ns.min_edits:
        reset_trail_counter(counter)
        sys.exit(0)
    trail = ns.trail or os.path.join(project_dir, "decisions.tsv")
    ok = False
    try:
        ok = (os.path.isfile(trail) and os.path.getsize(trail) > 0
              and datetime.date.fromtimestamp(os.path.getmtime(trail))
              == datetime.date.today())
    except OSError:
        ok = False
    if ok:
        reset_trail_counter(counter)
        sys.exit(0)
    strikes = read_trail_counter(counter) + 1
    if strikes > max(ns.max_blocks, 1):
        # Give up loudly: a gate that spins the agent forever is worse
        # than a missing trail. Counter resets so the next episode re-arms.
        reset_trail_counter(counter)
        msg = (f"决策轨迹仍缺失（已拦 {strikes - 1} 次达上限），本次放行不再阻停：{trail}。"
               "请尽快按 show-me-your-work 补 decisions.tsv。")
        sys.stderr.write(msg + "\n")
        log_block("trail-giveup", session_id, project_dir, msg)
        sys.exit(0)
    try:
        parent = os.path.dirname(counter)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(counter, "w", encoding="utf-8") as f:
            f.write(str(strikes))
    except OSError:
        pass
    fail(f"复杂工作（{edits} 次写操作）缺少当日决策轨迹：{trail}。"
         "按 show-me-your-work 写 decisions.tsv 后再结束。",
         kind="trail", project=project_dir)
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
             "按 show-me-your-work 写 decisions.tsv 后再结束。",
             kind="trail", project=project_dir)
    sys.exit(0)


def read_counter(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as f:
            return max(int(f.read().strip() or 0), 0)
    except (OSError, ValueError):
        return 0


def bump_counter(path: str) -> int:
    strikes = read_counter(path) + 1
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(strikes))
    except OSError:
        pass
    return strikes


def cmd_check_review(ns: argparse.Namespace) -> None:
    """Stop-hook mode: any source edit owes S5/S6 declaration artifacts.

    Requires <project>/.omc/verify-<session>.md (S5 evidence) and
    <project>/.omc/review-<session>.md (S6 verdict) when the transcript
    shows at least one non-.omc Edit/Write. Zero source edits, or an
    entry gate pinning delivery_target to patch, passes without artifacts.
    Same anti-spin ceiling as the trail check: at most --max-blocks
    blocks per episode, then give up loudly.
    """
    project_dir = ns.project_dir or ""
    raw = ""
    if not project_dir or not ns.transcript or not ns.session_id:
        raw = read_stdin_text()
    session_id = ns.session_id or ""
    payload = parse_stdin_json(raw)
    if not session_id:
        session_id = str(payload.get("session_id") or payload.get("sessionID") or "")
    if not project_dir:
        project_dir = str(payload.get("cwd") or payload.get("project_dir") or "")
        if not project_dir:
            project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    counter = review_counter_path(project_dir, session_id)
    transcript = read_transcript_text(ns.transcript, raw)
    if count_source_edits(transcript) < REVIEW_MIN_EDITS:
        reset_trail_counter(counter)
        sys.exit(0)
    if entry_gate_declares_patch(project_dir, session_id):
        reset_trail_counter(counter)
        sys.exit(0)
    problems: list[tuple[str, str, str]] = []
    for path, validator, kind in (
            (verify_artifact_path(project_dir, session_id), validate_verify, "verify"),
            (review_artifact_path(project_dir, session_id), validate_review, "review")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                reason = validator(f.read())
        except OSError:
            reason = f"缺失：{path}。"
        if reason is not None:
            problems.append((kind, path, reason))
    if not problems:
        reset_trail_counter(counter)
        sys.exit(0)
    strikes = read_counter(counter) + 1
    if strikes > max(ns.max_blocks, 1):
        reset_trail_counter(counter)
        kinds = "、".join(kind for kind, _, _ in problems)
        msg = (f"S5/S6 宣告仍缺失（{kinds}，已拦 {strikes - 1} 次达上限），"
               "本次放行不再阻停：请尽快补 .omc/verify-<session>.md 与 "
               ".omc/review-<session>.md。")
        sys.stderr.write(msg + "\n")
        log_block("review-giveup", session_id, project_dir, msg)
        sys.exit(0)
    bump_counter(counter)
    kind, path, reason = problems[0]
    hint = ("S6 无工件≈无门：有源码写操作就必须宣告 S5/S6。补两个小文件后再结束：\n"
            f"  {verify_artifact_path(project_dir, session_id)}"
            "（## 验证证据 + S4 ai-slop-cleaner 瘦身记录 + 命令/exit 条目）\n"
            f"  {review_artifact_path(project_dir, session_id)}"
            "（## 评审结论 + verdict + reviewer: + round: N + google-code-review 结论）\n"
            "micro 只需 3–5 行（约 15 秒），不许重述规则，只写实例。")
    fail(f"{reason}\n当前缺失或不合格：{path}\n{hint}",
         kind=kind, session=session_id, project=project_dir)


if __name__ == "__main__":
    main()
