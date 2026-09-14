# Entry Gate — Mechanical Enforcement

Deterministic counterpart of the SKILL.md "Entry Gate" section.
Prompt text is probabilistic (the agent may skip it); this hook is
deterministic (the tool call cannot proceed). Same philosophy as
`delivery-gate`: check machine-verifiable facts, never trust self-reports.

## R0 Read-only Recon

Read project instructions, repository/worktree state, active workflow records,
relevant code, and test entry points before committing scope or proof. Shell
and read tools remain allowed; file-write tools remain blocked until the gate
passes, except for the existing artifact self-exemption below. R0 itself is
read-only: an ungated shell is not permission to write files during recon.

After R0 and the Resume Gate, fresh or conflicting work writes the four-section
artifact before gated implementation edits. Resumed work reconciles its existing
gate with current evidence. Section 4 records:

```text
proof_mode + baseline/reproduction/unmet acceptance + exact verification commands
```

Choose intent-appropriate proof rather than requiring a failing unit test for
every task. For `delivery_target: patch`, keep all work read-only and return
the four sections and proposed patch in the response; no artifact is written
because no gated edit is attempted. These are policy semantics; the mechanical
checker continues to validate only the contract below.

## Contract

- Artifact: `<project>/.omc/entry-gate-<sessionID>.md` (sessionID in the
  filename kills stale-pass: yesterday's file never opens today's gate).
- Well-formed = 4 headers (`理解和假设` / `最小方案` / `范围纪律` /
  `验证计划` as `##` lines) + ≥1 list item (`-`/`*`/`1.`) under §2
  (the file-scope list) + ≥150 chars total.
- Blocked tool calls: file-write tools only (`Edit`/`Write` class — never
  match shell tools, or every test run would trip the gate).
- Self-exemption (no deadlock): writes targeting `.omc/entry-gate-*.md`
  itself always pass — the artifact IS the compliance action, so creating it
  cannot require it. Content is validated on subsequent edits to other files.
  The checker reads the write target from `--target`, stdin `tool_input`
  path fields (`file_path`/`filePath`/`path`/`TargetFile`/…), or Codex
  `apply_patch` (`*** Update File:`) text.
- No size exemption: micro-change writes the same 4 headers, one line each
  (≈30 seconds). The hook cannot judge task size before the first write,
  and a "micro, trust me" bypass would be gameable on day one.

One checker script serves all tools below — it speaks the industry-standard
hook protocol (JSON on stdin, exit 2 + stderr reason = block) and tolerates
missing fields (falls back to session `default` + process cwd):

```bash
mkdir -p ~/.claude/scripts
cp scripts/entry-gate-check.py ~/.claude/scripts/
```

All snippets below reference that canonical copy (cross-tool `~/.claude`
paths are already the norm on a shared machine — e.g. Trae hooks calling
`danger-guard.sh` from `~/.claude/hooks/`).
If you place it elsewhere, adjust the command paths.

Micro form (passes the checker):

```md
## 1. 理解和假设
把文档中的错别字 X 改成 Y；已读 AGENTS.md，R0 已定位该处；delivery_target 为 working_tree。

## 2. 最小方案
- 只改这一处，不碰周边。
- path/to/file.md

## 3. 范围纪律
只改该行；顺带问题只记录。

## 4. 验证计划
proof_mode：typo-search；改前基线命令 `rg -n -F 'X' path/to/file.md` 应命中目标行；改后同命令应无匹配（exit 1），`rg -n -F 'Y' path/to/file.md` 应命中更正内容，`git diff --check` 应通过。
```

(`NEW:` = yet-to-create files, skipped from existence checks.)

## Scope validation (first gated edit per session)

After the artifact passes, the checker validates the §2 file list once per
session (cached in `.omc/.scope-ok-<sessionID>`, re-runs when the artifact
is edited):

- Exists on disk → ok. `NEW:`-marked → ok. Outside project → block.
- Missing + project has `.codegraph/` index → `codegraph query` by symbol
  stem: hit → ok; miss → block (typo or missing `NEW:`).
- Missing + no index → block with the `NEW:` hint (forces explicitness,
  catches typos with zero dependencies).
- Broken codegraph CLI → warn + fail open (env issue must never deadlock).

## Trail check (Stop-hook mode, S8 teeth)

`--check-trail` reuses the checker for end-of-work enforcement:

```bash
python3 entry-gate-check.py --check-trail --project-dir <dir> \
  --transcript <transcript.jsonl>   # or stdin hook JSON with transcript_path
```

Small work (< 8 Edit/Write calls, `--min-edits` tunable) passes without a
trail. Complex work requires `<project>/decisions.tsv` (show-me-your-work
default, `--trail` to override): must exist, be non-empty, and be touched
today — else exit 2 blocks the stop. ("Today", not "this session": Stop hooks
cannot reliably know session start; same known limitation as delivery-gate.)
Anti-spin: at most `--max-blocks` blocks per episode (default 3), then it
gives up loudly (stderr + `trail-giveup` log row) and lets the stop through —
a gate that spins the agent forever is worse than a missing trail. Claude example (`Stop` event, keep any
existing Stop hooks):

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{ "type": "command",
                  "command": "python3 ~/.claude/scripts/entry-gate-check.py --check-trail",
                  "timeout": 15000 }]
    }]
  }
}
```

Same pattern maps 1:1 to Codex/Cursor/Trae/Qoder `Stop` (stdin
`transcript_path` is read automatically; `--project-dir` optional).
NOT auto-installed — Stop-hook wiring stays a deliberate manual step like
the write gate.

## Review check (Stop-hook mode, S6 teeth)

`--check-review` reuses the checker for S6 arrival enforcement — S6 无工件≈无门，
so every S6 must declare itself on disk:

```bash
python3 entry-gate-check.py --check-review --project-dir <dir> \
  --transcript <transcript.jsonl>   # or stdin hook JSON with transcript_path
```

Contracts (both live under `<project>/.omc/`, per-session filenames):

- `.omc/verify-<session>.md` (S5): one `##` heading containing `验证证据`,
  ≥1 list item (`-`/`*`/`1.`) naming a command and its exit code,
  包含 S4 收尾 `ai-slop-cleaner` (模式 B: deletion-first 瘦身) 执行记录, ≥80 chars total.
- `.omc/review-<session>.md` (S6): one `##` heading containing `评审结论`,
  a verdict token (`MERGE_READY` / `NEEDS_FIXES` / `ESCALATE`), a `reviewer:` line
  (name the model/human; no-baseline edits may write `self`), a `round: N` line
  (N ≥ 1, this round's review count), 包含 `google-code-review` 审查记录, ≥80 chars total.

Firing rule: count transcript toolUse blocks for real source edits
(`.omc/` artifact writes excluded; unreadable transcripts fall back to the
raw `Edit|Write` count, conservative). Zero source edits, or an entry gate
pinning `delivery_target` to `patch` (read-only route, no S6), passes without
artifacts. Otherwise a missing/malformed artifact exits 2 and blocks the stop.
Anti-spin mirrors the trail check: at most `--max-blocks` blocks per episode
(default 3), then loud give-up (`review-giveup` log row) and let the stop through.

Micro form (passes the checker, ~15 seconds):

```md
## S5 验证证据
- ai-slop-cleaner: deletion-first 瘦身完成，无冗余 wrapper 与死代码
- pytest tests/ → exit 0（3 passed）
- git diff --stat 确认仅保留必要修改

## S6 评审结论
verdict: MERGE_READY
reviewer: claude (self, no-baseline edit)
round: 1
google-code-review 无阻断项；health 豁免（无基线可比，见入口 §3）。
```

Claude example (`Stop` event, alongside the trail hook):

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{ "type": "command",
                  "command": "python3 ~/.claude/scripts/entry-gate-check.py --check-review",
                  "timeout": 15000 }]
    }]
  }
}
```

Same pattern maps 1:1 to Codex/Cursor/Trae/Qoder `Stop`. NOT auto-installed —
same manual-step rule as the write gate and the trail check.

## 1. Claude Code (one-time)

`~/.claude/settings.json` — add `PreToolUse` alongside existing hooks
(never delete the `Stop` gate):

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command",
                  "command": "python3 ~/.claude/scripts/entry-gate-check.py",
                  "timeout": 10000 }]
    }]
  }
}
```

## 2. Codex CLI (one-time)

`~/.codex/hooks.json` (new file; check with `/hooks` in the CLI afterwards):

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write|apply_patch",
      "hooks": [{ "type": "command",
                  "command": "python3 ~/.claude/scripts/entry-gate-check.py",
                  "timeout": 10 }]
    }]
  }
}
```

Caveat: hook input carries `session_id` + `cwd`, so the contract holds fully.
Third-party reports note intermittent `apply_patch` hook coverage — the
`Edit|Write` aliases in the matcher are the mitigation; `Bash` stays
unmatched on purpose (see Contract).

## 3. Cursor (one-time)

`~/.cursor/hooks.json` (new file; Cursor auto-reloads it):

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command",
                  "command": "python3 ~/.claude/scripts/entry-gate-check.py",
                  "timeout": 10 }]
    }]
  }
}
```

Cursor natively maps Claude hook names and honors exit-2 blocking.

## 4. Gemini CLI (one-time)

Merge into `~/.gemini/settings.json` (keep existing `mcpServers` etc.):

```json
{
  "hooks": {
    "BeforeTool": [{
      "matcher": "write_file|replace",
      "hooks": [{ "name": "entry-gate",
                  "type": "command",
                  "command": "python3 ~/.claude/scripts/entry-gate-check.py",
                  "timeout": 10000 }]
    }],
    "SessionStart": [{
      "matcher": "startup",
      "hooks": [{ "name": "entry-gate-reset",
                  "type": "command",
                  "command": "rm -f \"$GEMINI_PROJECT_DIR\"/.omc/entry-gate-*.md \"$GEMINI_PROJECT_DIR\"/.omc/.scope-ok-*" }]
    }]
  }
}
```

Caveat: `BeforeTool` input carries no session id, so the artifact falls back
to session `default` per project. The `SessionStart` cleanup above bounds
staleness to the current session — do not skip it.

## 5. Trae CN (one-time)

`~/.trae-cn/hooks.json` — append a group, keep existing groups (e.g. the
`matcher: *` danger-guard stays untouched):

```json
{
  "version": 1,
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command",
                  "command": "python3 ~/.claude/scripts/entry-gate-check.py",
                  "timeout": 10 }]
    }]
  }
}
```

Caveat (both verified live 2026-09-07 — either one alone fails silent):
1. Turn the group ON in Settings > Hooks. Hand-added groups default to OFF;
   the file being correct is not enough.
2. Set run-mode to 本地自动运行 (run outside sandbox), otherwise the checker
   cannot see the project directory.
Use absolute paths (`/Users/user/...`, not `~/...`) — Trae does not expand
`~` the way Claude/Codex do (proven live: `~` commands fail open, absolute
paths fire; pre-existing `danger-guard.sh` already uses absolute paths).
Restart Trae fully (Cmd+Q, not just closing windows) after editing hooks.json.

## 6. Antigravity (one-time, matcher to verify)

Antigravity's PreToolUse requires the verdict as JSON on **stdout**
(`{"decision": "deny"|"allow"}`) — a bare exit-2 fails OPEN there. Use the
adapter (it also maps `workspacePaths[0]` → project dir and
`conversationId` → session id, since Antigravity sends neither `cwd` nor
`session_id`):

```bash
cp scripts/entry-gate-antigravity.py ~/.claude/scripts/
```

`~/.gemini/config/hooks.json` (new file):

```json
{
  "entry-gate": {
    "PreToolUse": [{
      "matcher": "write_to_file",
      "hooks": [{ "type": "command",
                  "command": "python3 ~/.claude/scripts/entry-gate-antigravity.py",
                  "timeout": 10 }]
    }]
  }
}
```

Tool name `write_to_file` confirmed live via canary probe (08:44 capture:
`{"name":"write_to_file",...,"TargetFile":"/tmp/entry-gate-live-test.txt"}`).
Do NOT add `run_command` to the matcher — shell tools stay ungated by design.

## 7. Kimi Code (one-time, Beta)

Append to the hooks section of the Kimi config (`[[hooks]]` array syntax):

```toml
[[hooks]]
event = "PreToolUse"
matcher = "WriteFile|Edit"
command = "python3 ~/.claude/scripts/entry-gate-check.py"
timeout = 10
```

Caveat: hooks are a Beta feature and exact file-write tool names are taken
from docs examples — verify on first use, same as Antigravity.

## 8. Qoder (one-time)

Merge into `~/.qoder/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command",
                  "command": "python3 ~/.claude/scripts/entry-gate-check.py" }]
    }]
  }
}
```

No spaces inside the matcher (regex is literal). Timeout is fixed 30s.
Qoder passes `session_id` + `cwd`, so the contract holds fully.

## 9. OpenCode (one-time)

```bash
mkdir -p ~/.config/opencode/plugins ~/.config/opencode/scripts
cp plugins/entry-gate.ts ~/.config/opencode/plugins/
cp scripts/entry-gate-check.py ~/.config/opencode/scripts/
```

Plugin dir placement is enough (OpenCode loads
`~/.config/opencode/plugins/` automatically). Requires `python3` on PATH;
the plugin looks in `~/.claude/scripts/` first, then
`~/.config/opencode/scripts/` — override with `ENTRY_GATE_CHECKER` env.

## Verify an install (scratch dir, never the repo)

```bash
D=$(mktemp -d)
# 1. no artifact -> blocked (want exit 2 + reason on stderr)
echo '{"session_id":"demo","cwd":"'"$D"'"}' | python3 ~/.claude/scripts/entry-gate-check.py; echo "exit=$?"
# 2. write artifact (micro form above, session demo) into $D/.omc/, re-run -> exit 0
```

Then do one live pass in the real tool: start a session, attempt any file
edit, confirm the block message tells the agent to write the artifact.

## SessionStart memory brief (file-based, zero new systems)

`scripts/session-brief.py --project-dir <dir>` assembles existing memory
into a compact brief on stdout (all SessionStart-class events surface stdout
as context): ck `CONTEXT.md` excerpt (matched by path in `projects.json`),
wiki index + log tail, ledger breakpoint, trail freshness, 7-day block stats.
Missing stores print 无 and are skipped; always exits 0 (briefing never blocks).
`CK_HOME` / `ENTRY_GATE_BLOCKLOG` override paths (tests rely on this).

Claude example (`SessionStart`, keep existing groups):

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "hooks": [{ "type": "command",
                  "command": "python3 ~/.claude/scripts/session-brief.py --project-dir \"$CLAUDE_PROJECT_DIR\"",
                  "timeout": 10000 }]
    }]
  }
}
```

Same shape maps to Codex/Cursor/Gemini/Trae/Qoder `SessionStart` (their
project-dir variable in place of `$CLAUDE_PROJECT_DIR`). NOT auto-installed —
same manual-step rule as the write gate. It consumes the memory skills you
already run (`ck`, `wiki`, ledger, `decisions.tsv`); it creates no new store.

## Stop-hook trail wiring (per tool, `--check-trail` mode)

Small work (< 8 edits) passes without a trail; complex work without a fresh
`decisions.tsv` blocks the stop (max 3 blocks, then loud give-up).

- **Antigravity** — full support. `~/.gemini/config/hooks.json`, no matcher
  (Stop ignores it). The shim translates exit codes (0→`stop`, 2→`continue`,
  other→`stop` + warn) and maps `transcriptPath`→`--transcript` explicitly
  (Antigravity uses camelCase; the checker reads snake_case):
  ```json
  {
    "entry-gate-stop": {
      "Stop": [{
        "hooks": [{ "type": "command",
                    "command": "python3 ~/.claude/scripts/entry-gate-antigravity.py --stop",
                    "timeout": 30 }]
      }]
    }
  }
  ```
- **OpenCode** — warn-only (no blocking session event exists; only
  `tool.execute.before` can throw). The plugin counts edit/write per session
  and on `session.idle` fires a macOS notification + log (>= 8 edits, once
  per session). The human — not the hook — is the enforcement layer here;
  update `plugins/entry-gate.ts` (already included) and re-copy it.
- **ZCode** — no hook API found (`cli/config.json` = `{plugins, mcp}` only,
  `v2/setting.json` has no hook keys; surveyed 2026-09-07). Prompt-level
  Entry Gate + S5/S6 only. (Side find: its MCP list already contains
  `everme` memory + `sequential-thinking` — see memory rollout notes.)

## Block log & weekly report (value proof)

Every block appends one JSONL row (`ts/kind/session/project/reason`) to
`~/.claude/homunculus/entry-gate-blocks.jsonl` (`ENTRY_GATE_BLOCKLOG` or
`--block-log` overrides; logging never blocks the gate). Kinds: `missing` /
`malformed` / `scope` / `trail`.

```bash
python3 scripts/entry-gate-report.py [--log PATH] [--days 7]
```

Use the output to decide which gates earn their keep: a kind with zero
blocks for weeks is ceremony, not enforcement — cut it.

## Honest limitations

- Checks existence + structure, not truthfulness. Garbage artifacts are caught
  downstream by S5 evidence and S6 review (defense in depth).
- Shell-heredoc/redirect file writes bypass Edit/Write interception on every
  tool above. Same class of gap as delivery-gate's documented limits; S5/S6
  cover it. (Deliberately NOT matching shell tools: gating `Bash` would trip
  on every test run and paralyze the session.)
- Tools without a public hook API (ZCode, Grok, PI): prompt-level Entry Gate
  only — probabilistic, honestly labeled, S5/S6 still apply.
- Test suite: `scripts/test_entry_gate_check.py` (stdlib only, no pytest).
  Run it after any change to the checker: `python3 scripts/test_entry_gate_check.py`.
# test
