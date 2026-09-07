#!/usr/bin/env python3
"""Antigravity adapter for entry-gate-check.py.

Why this exists: Antigravity's PreToolUse contract requires the verdict as
JSON on stdout ({"decision": "allow"|"deny", ...}). A bare exit-2 with empty
stdout (the Claude/Codex/Cursor convention) fails OPEN there — the tool call
passes silently. This adapter translates.

Mapping (Antigravity -> checker):
  workspacePaths[0] -> --project-dir   (Antigravity sends no cwd)
  conversationId    -> --session-id    (per-conversation isolation)

Always exits 0 — the DECISION carries the verdict, never the exit code.
Stdlib only.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

CHECKER = os.environ.get(
    "ENTRY_GATE_CHECKER_BIN",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry-gate-check.py"))


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            payload = {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    workspaces = payload.get("workspacePaths") or []
    project_dir = workspaces[0] if workspaces else os.getcwd()
    session_id = str(payload.get("conversationId") or "default")

    argv = [sys.executable, CHECKER,
            "--project-dir", str(project_dir),
            "--session-id", session_id]
    tool_call = payload.get("toolCall") or {}
    tool_args = tool_call.get("args") or {}
    for key in ("TargetFile", "file", "path", "file_path"):
        val = tool_args.get(key)
        if isinstance(val, str) and val.strip():
            argv += ["--target", val.strip()]
            break

    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    except OSError as e:
        print(json.dumps({"decision": "deny", "reason": f"entry-gate checker failed to run: {e}"}))
        return

    if proc.returncode == 0:
        print(json.dumps({"decision": "allow"}))
    elif proc.returncode == 2:
        reason = (proc.stderr or "entry gate artifact missing or malformed").strip()
        print(json.dumps({"decision": "deny", "reason": reason}))
    else:
        # Checker crashed (not a validation verdict): fail OPEN, warn loudly.
        # A crashing gate must never brick the session (cf. delivery-gate).
        warn = f"entry-gate checker crashed (exit {proc.returncode}), fail-open"
        sys.stderr.write(warn + ": " + (proc.stderr or "").strip()[:200] + "\n")
        print(json.dumps({"decision": "allow", "reason": warn}))


if __name__ == "__main__":
    main()
