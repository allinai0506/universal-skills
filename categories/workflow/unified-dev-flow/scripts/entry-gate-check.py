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


def is_review_target(project_dir: str, target: str) -> bool:
    """True if target is a review artifact (.omc/review-*.md)."""
    if not target:
        return False
    abs_target = os.path.abspath(
        target if os.path.isabs(target) else os.path.join(project_dir, target))
    abs_proj = os.path.abspath(project_dir)
    if not _is_within(abs_proj, abs_target):
        return False
    parent, base = os.path.split(abs_target)
    return (os.path.basename(parent) == ".omc"
            and base.startswith("review-") and base.endswith(".md"))


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
    """S6 arrival declaration: heading + verdict + reviewer + round + review framework."""
    if not re.search(r"^##\s*.*评审结论", content, re.MULTILINE):
        return "缺少章节：评审结论（## 评审结论）。"
    if not re.search(r"\b(MERGE_READY|NEEDS_FIXES|ESCALATE)\b", content):
        return "评审结论缺少 verdict（MERGE_READY / NEEDS_FIXES / ESCALATE）。"
    m_rev = re.search(r"reviewer\s*[：:]\s*([^\n]+)", content, re.IGNORECASE)
    if not m_rev or not m_rev.group(1).strip():
        return "评审结论缺少 reviewer: 行（须注明独立审查模型或审视者）。"
    rev_val = m_rev.group(1).strip().lower()
    if re.search(r"\b(self|myself|me|main|main[-_]agent|author|self-review)\b", rev_val):
        return "评审结论 reviewer 不能为 self/主代理：S6 审查必须由独立 Reviewer 或独立审查子代理执行！"
    m = re.search(r"round\s*[：:]\s*(\d+)", content, re.IGNORECASE)
    if not m or int(m.group(1)) < 1:
        return "评审结论缺少 round: N 行（N ≥ 1，本轮评审计数）。"
    if not re.search(r"(?:google-code-review|xiyu-code-review|code-review|flow(?::|\s+)review)", content, re.IGNORECASE):
        return "缺少审查记录：S6 评审必须包含 google-code-review、xiyu-code-review、code-review 或 flow:review 审查结论。"
    if len(content) < REVIEW_MIN_CHARS:
        return f"评审结论过短（{len(content)} < {REVIEW_MIN_CHARS} 字）。"
    return None


def compute_diff_hash(project_dir: str, head_ref: str = "HEAD") -> str | None:
    """Compute sha256 hash of git diff from origin/main (or fallback base / <head_ref>~1 if not found)."""
    try:
        candidates = ("origin/main", "gitee/main", "main", "origin/master", "gitee/master", "master")
        base = None
        for candidate in candidates:
            res_base = subprocess.run(["git", "merge-base", candidate, head_ref],
                                      cwd=project_dir, capture_output=True, text=True, timeout=5)
            if res_base.returncode == 0 and res_base.stdout.strip():
                base = res_base.stdout.strip()
                break
        if not base:
            res_rev = subprocess.run(["git", "rev-parse", "--verify", f"{head_ref}~1"],
                                     cwd=project_dir, capture_output=True, text=True, timeout=5)
            if res_rev.returncode == 0 and res_rev.stdout.strip():
                base = res_rev.stdout.strip()
        if not base:
            return None

        res_diff = subprocess.run(["git", "diff", f"{base}..{head_ref}"],
                                  cwd=project_dir, capture_output=True, text=True, timeout=10)
        if res_diff.returncode == 0:
            import hashlib
            return hashlib.sha256(res_diff.stdout.encode("utf-8")).hexdigest()
    except Exception:
        pass
    return None


def validate_review_provenance(project_dir: str, review_content: str,
                               head_ref: str = "HEAD") -> str | None:
    """Validate that review provenance matches the git state of head_ref.
    If diff_hash is present in the review, it must match the diff of head_ref.
    """
    m_diff = re.search(r"diff_hash\s*[：:]\s*([a-f0-9]{64})", review_content, re.IGNORECASE)
    if m_diff:
        expected_diff_hash = m_diff.group(1).strip()
        current_diff_hash = compute_diff_hash(project_dir, head_ref)
        if current_diff_hash and current_diff_hash != expected_diff_hash:
            return (f"S6 评审凭证已失效：检测到代码在审查后发生变更（diff_hash 不匹配）！\n"
                    f"  凭据中的 hash: {expected_diff_hash[:12]}...\n"
                    f"  当前的 diff hash: {current_diff_hash[:12]}...\n"
                    "  【铁律】任何源码修改都会导致先前的审查证据失效。必须重新执行 S6 Code Review！")
    return None


def verify_transcript_reviewer(transcript_text: str) -> tuple[bool, str]:
    """Scan transcript for independent reviewer execution:
    1. invoke_subagent with role matching Reviewer / code-review; or
    2. execution of flow:review / xiyu-code-review / google-code-review.
    """
    if not transcript_text:
        return True, ""

    if re.search(r'"invoke_subagent"', transcript_text) or re.search(r'"name":\s*"invoke_subagent"', transcript_text):
        if re.search(r'"[Rr]ole":\s*"[^"]*(?:[Rr]eview|审|audit)[^"]*"', transcript_text):
            return True, ""
        if re.search(r'"TypeName":\s*"[^"]*(?:[Rr]eview|code-review)[^"]*"', transcript_text):
            return True, ""

    if re.search(r'flow(?::|\s+)review|xiyu-code-review|google-code-review', transcript_text):
        return True, ""

    return False, ("Transcript 审计发现：本次会话中未检测到独立 Reviewer 子代理（invoke_subagent）调用，"
                  "亦未检测到 flow:review / xiyu-code-review 审查命令执行记录！"
                  "严禁主 Agent 自行撰写审查结论，必须派遣独立审查者。")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-trail", action="store_true")
    ap.add_argument("--check-review", action="store_true")
    ap.add_argument("--guard-pr", action="store_true")
    ap.add_argument("--guard-push", action="store_true")
    ap.add_argument("--guard-commit", action="store_true")
    ap.add_argument("--record-review", action="store_true")
    ap.add_argument("--reviewer", default="")
    ap.add_argument("--verdict", default="MERGE_READY")
    ap.add_argument("--notes", default="")
    ap.add_argument("--branch", default="")
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
    if early.guard_pr:
        cmd_guard_pr(early)
        return
    if early.guard_push:
        cmd_guard_push(early)
        return
    if early.guard_commit:
        cmd_guard_commit(early)
        return
    if early.record_review:
        cmd_record_review(early)
        return
    project_dir, session_id, target = resolve_context(argv)
    if target and is_review_target(project_dir, target):
        fail("[DENY 权限拦截]: 主 Agent 无权直接手写或修改 S6 审查工件 (.omc/review-*.md)！\n"
             "【铁律】裁判不能由选手兼任。S6 Code Review 必须由独立 Reviewer 子代理（invoke_subagent）评估，"
             "或通过 flow:review / xiyu-code-review CLI 工具由外部独立进程生成并落盘。\n"
             "严禁主 Agent 调用写工具自审伪造审查凭据！",
             kind="review-write-forbidden", session=session_id, project=project_dir)
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
    hint = ("S5/S6 阶段工件缺失：源码写操作完成后，必须完成验证 + 独立审查才能结束会话。\n"
            f"  1. 验证工件: {verify_artifact_path(project_dir, session_id)}\n"
            "     （## 验证证据 章节 + S4 ai-slop-cleaner 瘦身记录 + 命令/exit code 列表）\n"
            f"  2. 审查工件: {review_artifact_path(project_dir, session_id)}\n"
            "     （必须通过 flow:review / google-code-review / xiyu-code-review 独立审查工具生成，\n"
            "      严禁主 Agent 自行手写此文件！）\n"
            "  【铁律】主 Agent 不能自证清白，审查者必须独立于编码者。")
    fail(f"{reason}\n当前缺失或不合格：{path}\n{hint}",
         kind=kind, session=session_id, project=project_dir)


def find_latest_omc_pair(project_dir: str, session_id: str = "") -> tuple[str | None, str | None, str | None]:
    """Find (verify_path, review_path, discovered_session) under <project_dir>/.omc/.
    If session_id is given, checks those paths directly.
    Otherwise scans for newest review-*.md and matching/newest verify-*.md.
    """
    omc_dir = os.path.join(project_dir, ".omc")
    if not os.path.isdir(omc_dir):
        return None, None, None
    if session_id:
        v_path = os.path.join(omc_dir, f"verify-{session_id}.md")
        r_path = os.path.join(omc_dir, f"review-{session_id}.md")
        return (v_path if os.path.isfile(v_path) else None,
                r_path if os.path.isfile(r_path) else None,
                session_id)

    review_files: list[tuple[float, str, str]] = []
    for fname in os.listdir(omc_dir):
        if fname.startswith("review-") and fname.endswith(".md"):
            p = os.path.join(omc_dir, fname)
            try:
                review_files.append((os.path.getmtime(p), p, fname[7:-3]))
            except OSError:
                pass
    if not review_files:
        return None, None, None
    review_files.sort(key=lambda x: x[0], reverse=True)
    best_review = review_files[0][1]
    best_session = review_files[0][2]

    v_path = os.path.join(omc_dir, f"verify-{best_session}.md")
    if os.path.isfile(v_path):
        return v_path, best_review, best_session

    verify_files: list[tuple[float, str]] = []
    for fname in os.listdir(omc_dir):
        if fname.startswith("verify-") and fname.endswith(".md"):
            p = os.path.join(omc_dir, fname)
            try:
                verify_files.append((os.path.getmtime(p), p))
            except OSError:
                pass
    best_verify = max(verify_files, key=lambda x: x[0])[1] if verify_files else None
    return best_verify, best_review, best_session


def cmd_guard_commit(ns: argparse.Namespace) -> None:
    """Pre-commit hook: enforce branch-specific Entry Gate artifact exists.

    Replaces the old glob-based ls .omc/entry-gate-*.md which allowed any
    historical file to satisfy the gate. Now binds strictly to the current
    git branch name, preventing stale .omc/ directory pollution from leaking
    through.

    Exit codes: 0 = pass, 1 = block
    """
    project_dir = ns.project_dir or os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    # Detect current branch
    try:
        res = subprocess.run(["git", "branch", "--show-current"],
                             cwd=project_dir, capture_output=True, text=True, timeout=5)
        branch = res.stdout.strip() if res.returncode == 0 else ""
    except Exception:
        branch = ""

    # Sanitize branch name for filesystem use
    safe_branch = re.sub(r"[^A-Za-z0-9_-]", "_", branch) if branch else ""

    if safe_branch:
        # Strict branch-bound check: require .omc/entry-gate-<branch>.md
        branch_gate = os.path.join(project_dir, ".omc", f"entry-gate-{safe_branch}.md")
        if os.path.isfile(branch_gate):
            # Validate content
            try:
                with open(branch_gate, "r", encoding="utf-8") as f:
                    content = f.read()
                reason = validate(content)
                if reason is None:
                    sys.stdout.write(f"✅ [pre-commit] Entry Gate (branch: {branch}): {branch_gate}\n")
                    sys.exit(0)
                else:
                    sys.stderr.write(
                        f"❌ [unified-dev-flow 阻断]: 分支入口工件不合格！\n"
                        f"  分支: {branch}\n  文件: {branch_gate}\n  原因: {reason}\n"
                    )
                    sys.exit(1)
            except OSError as e:
                sys.stderr.write(f"❌ 无法读取分支入口工件: {branch_gate} ({e})\n")
                sys.exit(1)
        else:
            # Fall back to session-based artifact (for agents without branch naming)
            session_id = ns.session_id or "default"
            session_gate = artifact_path(project_dir, session_id)
            if os.path.isfile(session_gate):
                try:
                    with open(session_gate, "r", encoding="utf-8") as f:
                        content = f.read()
                    if validate(content) is None:
                        sys.stdout.write(f"✅ [pre-commit] Entry Gate (session-bound): {session_gate}\n")
                        sys.exit(0)
                except OSError:
                    pass
            # No valid artifact found for current branch
            msg = (
                f"\n❌ [unified-dev-flow 阻断]: 当前分支「{branch}」没有专属入口工件！\n"
                f"  期望文件: {os.path.join('.omc', f'entry-gate-{safe_branch}.md')}\n"
                "  【必须前置】: 提交业务源码前，必须先写入专属分支入口工件，声明：\n"
                "    1. 理解和假设\n    2. 最小方案 + 文件范围\n    3. 范围纪律\n    4. 验证计划\n"
                f"  （旧会话的 .omc/entry-gate-*.md 不满足当前分支「{branch}」的门禁需求）\n"
            )
            sys.stderr.write(msg)
            sys.exit(1)
    else:
        # No branch info: fall back to session-based check
        session_id = ns.session_id or "default"
        path = artifact_path(project_dir, session_id)
        if not os.path.isfile(path):
            sys.stderr.write(f"❌ [unified-dev-flow 阻断]: 缺少入口工件: {path}\n")
            sys.exit(1)
        sys.exit(0)


def cmd_record_review(ns: argparse.Namespace) -> None:
    """Write S6 review artifact from an authorized external reviewer.

    This command is the ONLY sanctioned way for the main agent to write
    a review artifact. It requires:
      - --reviewer: the independent reviewer identity (not 'self')
      - --verdict: MERGE_READY / NEEDS_FIXES / ESCALATE
      - The review must originate from a subagent or external tool call,
        validated by transcript-based evidence.

    The generated artifact is stamped with the diff_hash of the current
    repository state to detect post-review code modifications.
    """
    project_dir = ns.project_dir or os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    session_id = re.sub(r"[^A-Za-z0-9_-]", "_", ns.session_id or "default")
    reviewer = (ns.reviewer or "").strip()
    verdict = (ns.verdict or "MERGE_READY").strip().upper()
    notes = (ns.notes or "").strip()

    if not reviewer:
        sys.stderr.write("❌ [record-review] --reviewer 必填：必须指明独立审查者身份\n")
        sys.exit(1)
    if re.search(r"\b(self|myself|me|main|main[-_]agent|author|self-review)\b", reviewer.lower()):
        sys.stderr.write("❌ [record-review] reviewer 不能为 self/主代理：S6 审查必须由独立 Reviewer 执行！\n")
        sys.exit(1)
    if verdict not in ("MERGE_READY", "NEEDS_FIXES", "ESCALATE"):
        sys.stderr.write(f"❌ [record-review] 无效 verdict: {verdict}。必须是 MERGE_READY / NEEDS_FIXES / ESCALATE\n")
        sys.exit(1)

    diff_hash = compute_diff_hash(project_dir) or "unknown"
    review_path = review_artifact_path(project_dir, session_id)
    os.makedirs(os.path.dirname(review_path), exist_ok=True)
    content = (
        "## 评审结论\n\n"
        f"verdict: {verdict}\n"
        f"reviewer: {reviewer}\n"
        "round: 1\n"
        f"diff_hash: {diff_hash}\n"
        "code-review: flow:review 独立子代理审查\n\n"
        f"{notes}\n"
    )
    try:
        with open(review_path, "w", encoding="utf-8") as f:
            f.write(content)
        sys.stdout.write(
            f"✅ [record-review] S6 评审工件已生成\n"
            f"   reviewer: {reviewer} | verdict: {verdict}\n"
            f"   diff_hash: {diff_hash[:16]}...\n"
            f"   文件: {review_path}\n"
        )
        sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"❌ [record-review] 无法写入评审工件: {review_path} ({e})\n")
        sys.exit(1)


def cmd_guard_pr(ns: argparse.Namespace) -> None:
    """PR / Push Gate: Verify S6 Code Review is passed with MERGE_READY before PR or Push.

    Exit codes:
      0 = pass (allows PR creation or git push)
      1 = block (rejects operation with guidance to run S6 review)
    """
    project_dir = ns.project_dir or ""
    if not project_dir:
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    # 逃生阀 (Emergency escape hatch)
    if os.environ.get("UNIFIED_DEV_FLOW_SKIP_REVIEW") == "1" or os.environ.get("UNIFIED_DEV_FLOW_FORCE") == "1":
        sys.stderr.write("⚠️ [unified-dev-flow] 检测到 UNIFIED_DEV_FLOW_SKIP_REVIEW=1，跳过 S6 Review 门禁（已记录逃生事件）\n")
        log_block("review-bypass", ns.session_id or "bypass", project_dir, "UNIFIED_DEV_FLOW_SKIP_REVIEW=1")
        sys.exit(0)

    branch = ns.branch or ""
    if not branch:
        try:
            res = subprocess.run(["git", "branch", "--show-current"],
                                 cwd=project_dir, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                branch = res.stdout.strip()
        except Exception:
            branch = ""

    verify_path, review_path, discovered_session = find_latest_omc_pair(project_dir, ns.session_id)
    if not ns.session_id and discovered_session:
        ns.session_id = discovered_session
    if not review_path or not os.path.isfile(review_path):
        msg = (
            "\n"
            "╔══════════════════════════════════════════════════════════════════════════════╗\n"
            "║  ⛔ [unified-dev-flow 门禁阻断] 尚未执行 S6 Code Review，禁止创建 PR / 推送！  ║\n"
            "╚══════════════════════════════════════════════════════════════════════════════╝\n"
            f"  项目目录: {project_dir}\n"
            f"  当前分支: {branch or 'unknown'}\n"
            "  【缺失工件】: .omc/review-*.md (S6 评审结论)\n\n"
            "  【立即行动指南】:\n"
            "  1. 运行 S6 Code Review：调用 xiyu-code-review 或 google-code-review 执行三透镜独立审查；\n"
            "  2. 生成工件：.omc/review-<session>.md（须包含 ## 评审结论、verdict: MERGE_READY、reviewer、round）与 .omc/verify-<session>.md；\n"
            "  3. 确认评审结论为 MERGE_READY 后，方可重新提交 PR 或推送分支。\n"
            "  （紧急逃生阀: 仅限生产抢修故障时设置 UNIFIED_DEV_FLOW_SKIP_REVIEW=1）\n"
        )
        sys.stderr.write(msg + "\n")
        log_block("guard-pr-missing", ns.session_id or "default", project_dir, "review artifact missing")
        sys.exit(1)

    try:
        with open(review_path, "r", encoding="utf-8") as f:
            review_content = f.read()
    except OSError as e:
        sys.stderr.write(f"⛔ [unified-dev-flow 门禁阻断]: 无法读取评审工件: {review_path} ({e})\n")
        sys.exit(1)

    reason = validate_review(review_content)
    if reason:
        msg = (
            f"⛔ [unified-dev-flow 门禁阻断]: S6 评审工件不合规！\n"
            f"  文件: {review_path}\n"
            f"  原因: {reason}\n"
            "  请按规范完善 S6 评审结论（需含 ## 评审结论、verdict、reviewer:、round: N、审查记录）。"
        )
        sys.stderr.write(msg + "\n")
        log_block("guard-pr-malformed", ns.session_id or "default", project_dir, reason)
        sys.exit(1)

    m_verdict = re.search(r"\b(MERGE_READY|NEEDS_FIXES|ESCALATE)\b", review_content)
    verdict = m_verdict.group(1) if m_verdict else "UNKNOWN"
    if verdict != "MERGE_READY":
        msg = (
            f"⛔ [unified-dev-flow 门禁阻断]: 当前 S6 评审结论为 {verdict}，未达到 MERGE_READY 交付标准！\n"
            f"  文件: {review_path}\n"
            "  【处置要求】:\n"
            "    • 若为 NEEDS_FIXES: 必须回到 S4 修复问题，S5 重新验证，S6 重新审查，直至达成 MERGE_READY。\n"
            "    • 若为 ESCALATE: 需升级人工确认，禁止自动创建 PR。\n"
        )
        sys.stderr.write(msg + "\n")
        log_block("guard-pr-verdict", ns.session_id or "default", project_dir, f"verdict is {verdict}")
        sys.exit(1)

    if not verify_path or not os.path.isfile(verify_path):
        msg = (
            "⛔ [unified-dev-flow 门禁阻断]: 缺少 S5 验证证据工件（.omc/verify-*.md）！\n"
            "  请确保 S4 ai-slop-cleaner 瘦身与 S5 测试执行记录完整写入 .omc/verify-<session>.md。"
        )
        sys.stderr.write(msg + "\n")
        log_block("guard-pr-verify-missing", ns.session_id or "default", project_dir, "verify artifact missing")
        sys.exit(1)

    try:
        with open(verify_path, "r", encoding="utf-8") as f:
            verify_content = f.read()
    except OSError as e:
        sys.stderr.write(f"⛔ [unified-dev-flow 门禁阻断]: 无法读取验证工件: {verify_path} ({e})\n")
        sys.exit(1)

    v_reason = validate_verify(verify_content)
    if v_reason:
        msg = (
            f"⛔ [unified-dev-flow 门禁阻断]: S5 验证证据工件不合规！\n"
            f"  文件: {verify_path}\n"
            f"  原因: {v_reason}\n"
        )
        sys.stderr.write(msg + "\n")
        log_block("guard-pr-verify-malformed", ns.session_id or "default", project_dir, v_reason)
        sys.exit(1)

    # Diff hash provenance check: if review has a diff_hash, verify it matches current state
    # In pre-push mode head_ref is the pushed object, not cwd HEAD (push ≠ checkout)
    head_ref = getattr(ns, "head_ref", "") or "HEAD"
    prov_reason = validate_review_provenance(project_dir, review_content, head_ref=head_ref)
    if prov_reason:
        sys.stderr.write(f"⛔ [unified-dev-flow 门禁阻断]: {prov_reason}\n")
        log_block("guard-pr-stale-review", ns.session_id or "default", project_dir, prov_reason[:200])
        sys.exit(1)

    # Transcript reviewer verification: if transcript is available, check reviewer was independent
    transcript_text = ""
    if ns.transcript:
        transcript_text = read_transcript_text(ns.transcript)
    if not transcript_text:
        # Try AGY default path
        conv_id = ns.session_id or ""
        if conv_id:
            agy_transcript = os.path.expanduser(
                f"~/.gemini/antigravity-cli/brain/{conv_id}/.system_generated/logs/transcript.jsonl"
            )
            if os.path.isfile(agy_transcript):
                transcript_text = read_transcript_text(agy_transcript)

    if transcript_text:
        ok, transcript_reason = verify_transcript_reviewer(transcript_text)
        if not ok:
            sys.stderr.write(f"⛔ [unified-dev-flow 门禁阻断]: {transcript_reason}\n")
            log_block("guard-pr-no-independent-reviewer", ns.session_id or "default",
                      project_dir, transcript_reason[:200])
            sys.exit(1)

    sys.stdout.write(
        f"✅ [unified-dev-flow 门禁放行] S6 Code Review 验证通过: verdict=MERGE_READY\n"
        f"   评审工件: {os.path.basename(review_path)} | 验证工件: {os.path.basename(verify_path)}\n"
    )
    sys.exit(0)


def cmd_guard_push(ns: argparse.Namespace) -> None:
    """Git pre-push hook mode.
    Reads lines from stdin: <local ref> <local sha1> <remote ref> <remote sha1>.
    """
    raw = read_stdin_text()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    if not lines:
        cmd_guard_pr(ns)
        return

    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        local_ref, local_sha, remote_ref, remote_sha = parts[:4]
        # 删除远端分支操作不阻断
        if local_sha == "0000000000000000000000000000000000000000" or local_ref == "(delete)":
            continue
        ref_name = local_ref.replace("refs/heads/", "")
        # 如果是主干/保护分支，pre-push 本身不在此阻断（由专用保护策略处理）
        if ref_name in ("main", "master"):
            continue
        # 对开发任务分支（agent/*, feat/*, fix/*, 或其它开发分支）必须检查 S6
        ns.branch = ref_name
        # provenance 必须哈希被推送的对象而非 cwd HEAD：git push 可推送当前未 checkout 的分支
        if re.fullmatch(r"[0-9a-f]{6,64}", local_sha, re.IGNORECASE):
            ns.head_ref = local_sha
        cmd_guard_pr(ns)
        return

    # 若全是已排除 ref，直接放行
    sys.exit(0)


if __name__ == "__main__":
    main()
