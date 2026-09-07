# Implementation Notes

## Task: unify global skills through symlinks

Branch: `chore/unify-global-skill-symlinks`

## Understanding and assumptions

- `~/universal-skills/categories/` is the canonical local source for shared skills.
- Global tool skill directories should not keep duplicate copies of these skills when symlinks are supported.
- ZCode/Agents-managed built-in or well-known skills under `~/.agents/skills/` must be preserved. The sync script should only add universal-skills symlinks there and skip existing non-symlink entries.
- Cursor `.mdc` rules and Claude plugin cache are generated integration artifacts; they are not treated as duplicate source-of-truth skill folders.

## Decisions

- Changed Claude global skill sync from `cp -r` to per-skill symlinks so future runs do not recreate duplicate skill copies.
- Extended ZCode sync to also normalize `~/.zcode/skills/` symlinks to point directly at `~/universal-skills/categories/...`, instead of relying on a second hop through `~/.codex/skills/...`.
- Kept `~/.agents/skills/` as incremental-only sync to avoid deleting or overwriting ZCode/Agents built-in and well-known skills.
- Did not touch unrelated modified skill content in `categories/deployment/xiyu-server-deploy/SKILL.md`.

## Verification plan

- Run `bash -n sync.sh`.
- Run `bash sync.sh --no-projects --no-codex --no-gemini --no-kimi` to exercise Claude global/plugin sync and ZCode sync without broader project/network work.
- Verify `~/.claude/skills` contains symlinks and no copied skill directories.
- Verify representative `~/.zcode/skills/*` entries point directly to `~/universal-skills/categories/...`.
- Verify no broken symlinks in `~/.claude/skills`, `~/.zcode/skills`, and `~/.agents/skills`.
- Verify built-in ZCode/Agents skills such as `gstack`, `lark-doc`, and `autoplan` still have `SKILL.md` files.

## Task: optimize xiyu-server-deploy skill

## Decisions

- Added the requested direct server connectivity probe to `categories/deployment/xiyu-server-deploy/SKILL.md` under target environment establishment, because it is a safe read-only access check and belongs before deployment actions.
- Used `StrictHostKeyChecking=accept-new` rather than the older imported skill's `StrictHostKeyChecking=no` pattern, because it keeps first-connect convenience without permanently disabling host key verification.
- Kept the imported `xiyu-deploy` file unchanged; it appears to be an older, project-specific operational note rather than the canonical deployment workflow.

## Task: migrate xiyu-deploy imported details

## Decisions

- Migrated concrete non-secret environment details from `categories/imported/xiyu-deploy/SKILL.md` into `categories/deployment/xiyu-server-deploy/references/release-runbook.md` under a `Known Winbid Test Server` section.
- Did not copy literal smoke-test credentials from the imported skill. The runbook now explicitly warns not to record smoke passwords, DB passwords, Redis passwords, private keys, or copied env contents.
- Preserved the legacy key path and legacy SSH option pattern only as fallback guidance, while keeping `StrictHostKeyChecking=accept-new` as the preferred direct-probe/default.
- Summarized the old hand-written scp/systemctl steps rather than copying them verbatim, because the canonical runbook already prefers GitHub Actions and `scripts/release/remote-deploy.sh`.

## Task: optimize unified-dev-flow skill

## Findings

- `categories/security-review/SKILL.md` was single-level, but every `sync.sh` loop uses `categories/*/*` — the skill was never installed anywhere (`~/.config/opencode/skills/security-review` missing). S6 referenced a dead link.
- SKILL.md mandated `google-code-review` while WORKFLOW-MAP.md §2 claimed canonical was engineering `code-review`; SKILL never mentioned `code-review` at all.
- Medium route diverged: SKILL said `speckit-chain`, MAP §4 said hand-split `writing-plans` route; MAP §4 also lacked refactor/research rows that SKILL has.
- `WORKFLOW-MAP.md at the repo root` pointer was unreachable after install (flat per-skill symlinks).
- S0 missed the AGENTS.md ledger breakpoint-resume rule; S3→S4 exemption covered micro only while the small route also skips S3; `ai-release-engineer` gate covered all AI-assisted code (≈ everything); Intractable route listed标讯-specific `blueprint-driven-development` as generic fallback.
- `categories/imported/ai-slop-cleaner/` was an empty leftover dir.

## Decisions

- Moved skill to `categories/security/security-review/` via `git mv` (history preserved as `R`); deleted the empty imported dir; fixed the stale `security-review/` line in AGENTS.md.
- S6 rule kept as validated (`ai-slop-cleaner` + `google-code-review` mandatory) and added `code-review` as spec-consistency supplement for spec-bearing routes only; MAP §2 updated to match instead of contradicting.
- MAP §4 rewritten to SKILL's taxonomy (added refactor/research rows, bug keeps S6-light, medium/large use `speckit-chain`, large makes `architect` plan review explicit).
- Created `categories/workflow/unified-dev-flow/references/alternatives.md` (stage alternatives + domain table + debug ladder, all refs machine-verified) and repointed SKILL.md's Overview at it; installed copies get it free via whole-dir symlink.
- S0 now checks `.superpowers/sdd/progress.md` first (resume, no re-classify); exemption widened to micro+small with S5 never exempt; `ai-release-engineer` narrowed to `autopilot`/`ralph` unattended output; Intractable keeps `figure-it-out` only (blueprint users invoke it by name, covered by When-NOT-to-use).
- P2: S6 force-semantics live only in Gates; dropped the duplicate access-pattern bullet (kept in S3 + debug note in references); standing principles named (4) with rest on-demand; parallel trio disambiguated; description gained one English trigger sentence with no flow enumeration (article's probe lesson preserved); `standard-workflow` non-intercept declared.
- Also fixed stale `gstack-*` names in MAP (§2 S2/S6/S7: `spec`, `qa`/`qa-only`, `ship`, `canary` — verified against frontmatter).
- Left untouched: `skillify` duplicate (`categories/gstack/skillify` vs `categories/imported/skillify`, both `name: skillify`) — pre-existing, needs its own DUPLICATE_SKILL_NAMES decision; sync run refreshed an alias symlink inside the gstack dir, flagged as follow-up.

## Verification plan

- `quick_validate.py` on both touched skills → valid.
- Regex-extracted all backtick skill refs from SKILL.md (69) and alternatives.md (64) → all resolve to exactly one `categories/*/*/SKILL.md`, no duplicates.
- `./sync.sh --no-projects` → all global targets OK, `security-review` symlink now present in `~/.config/opencode/skills/` and `~/.claude/skills/`, SKILLS-INDEX.md + GEMINI.md rebuilt (`### security` section, real description).
- Project checkouts still hold old file copies (`--no-projects`); next full `./sync.sh` propagates.

## Task: stop generating Cursor skill rules

## Decisions

- Disabled the `sync_cursor_projects` call in `sync.sh` so future sync runs no longer generate `.cursor/rules/*.mdc` skill files.
- Left the `sync_cursor_projects` function in place for now rather than deleting it, so the behavior can be restored or converted into an explicit opt-in flag later with minimal risk.
- Updated `AGENTS.md` and `CLAUDE.md` to say Cursor skill rule generation is no longer part of the normal sync behavior.
- Did not delete existing project `.cursor/rules/*.mdc` files automatically because those are outside this repository and may include non-skill Cursor rules; cleanup should be a separate confirmed action.

## Task: sync Trae CN Agent skills

## Decisions

- Added Trae CN Agent as a first-class sync target at `~/.trae-cn/skills/` after confirming that directory exists locally and contains Trae-managed marketplace skills.
- Used incremental symlink sync rather than deleting/recreating the directory, because Trae CN stores marketplace and built-in skills in the same area and those should not be overwritten.
- Added `--no-trae-cn` for parity with other optional sync targets.
- Existing Trae CN non-symlink skills with the same name as universal skills are skipped, so Trae-managed marketplace installs remain authoritative unless manually removed.

## Task: remove duplicate Agent-visible skill copies

## Findings

- ZCode/Agent-visible skills were duplicated because both `~/.agents/skills/` and legacy `~/.zcode/skills/` contained universal-skills symlinks.
- `~/.zcode/skills/` was entirely universal-skills symlinks, so it acted as a second copy of the same skill set for agents that scan both locations.
- Some non-symlink skills remain under `~/.agents/skills/` and `~/.trae-cn/skills/`; those are tool-managed built-in/marketplace skills and are intentionally not removed automatically.

## Decisions

- Kept `~/.agents/skills/` as the single ZCode/Agent universal-skills sync target.
- Changed sync to remove old universal-skills symlinks from `~/.zcode/skills/` instead of recreating them.
- Did not delete non-symlink skills in `~/.agents/skills/` or `~/.trae-cn/skills/`, because those may be installed or managed by the tools themselves.

## Task: hide near-duplicate skills from sync targets

## Findings

- `categories/workflow/google-code-review/SKILL.md` and `categories/coding/google-style-code-review/SKILL.md` both declare `name: google-code-review` and contain highly overlapping Google-style review guidance.
- Frontmatter-name duplicate scan also reports `skill-creator` and `skill-installer` under both workflow and `.system`; those `.system` copies are not currently synced by the `categories/*/*` loops, so they are not part of the visible duplicate issue.

## Decisions

- Added an explicit `DUPLICATE_SKILL_NAMES` list in `sync.sh` instead of trying fuzzy matching at sync time. This keeps the behavior deterministic and avoids accidentally hiding unrelated skills with similar words.
- Added `google-style-code-review` to that list, keeping `workflow/google-code-review` as the canonical visible skill because both files use that canonical frontmatter name.
- Kept the duplicate source directory in the repository for now rather than deleting it automatically; sync targets now skip it and clean old universal-skills symlinks pointing to it.
- Applied the filter to Claude global/project/plugin, Codex, ZCode, Trae CN, and Kimi symlink sync paths.

## Task: fix post-commit hook hardcoded origin

## Decisions

- Hook step 3 hardcoded `git push origin "$branch"`, but this repo's remote is named `gitee` (no `origin`), so every commit's push step failed with "fatal: 'origin' does not appear to be a git repository".
- Replaced with upstream-aware detection: `git rev-parse --abbrev-ref @{u}` → fall back to first remote in `git remote` → skip if none. Works regardless of remote name.
- Updated wording from "推送到 GitHub" to "推送到远端" since the actual remote is Gitee, not GitHub.

## Task: unified-dev-flow entry gate + mechanical enforcement

Branch: `feat/unified-dev-flow-entry-gate`

## Findings

- Prompt-only gates get skipped under pressure (admitted in SKILL.md Common mistakes for S6); enforcement must be deterministic code on the tool-call path, not more text.
- Repo had only git hooks (post-commit sync); agent-behavior precedent exists as `delivery-gate` (Stop hook + quality-gate.py, exit-2 block, stdin transcript_path) — reused its philosophy and stdlib-only style.
- OpenCode plugins expose `tool.execute.before` (throw = block) with sessionID + project dir; Claude has PreToolUse. Both can gate the first Edit/Write.

## Decisions

- Entry Gate compressed 6 items → 4, each pinned to exactly one downstream consumer (①→S1/S2 ②→S3 ③→S6 ④→S5) + anti-restatement rule (instantiate, never restate) to remove the overlap burden instead of adding ceremony.
- Mechanical contract: `<project>/.omc/entry-gate-<sessionID>.md` (session in filename kills stale-pass), 4 headers + file list under §2 + ≥150 chars; single source of truth `scripts/entry-gate-check.py`, thin TS wrapper `plugins/entry-gate.ts` shells out to it.
- DEVIATION from A2 (micro exempt): hook enforces uniformly — it cannot judge task size before the first write and any self-declared bypass is gameable. Micro cost is 4 one-liners (~30s); template in references/enforcement.md. One-line revert possible if rejected.
- Entry item ① requires naming project constraint docs read (RULES.md / lessons-learned.md / AGENTS.md, if present) — the global-router vs project-docs split the user clarified.
- Honest limits documented (existence≠truth; bash-redirect bypass) — downstream S5/S6 are the second layer, same defense-in-depth as delivery-gate + self-audit.
- TDD: `scripts/test_entry_gate_check.py` written first (RED: script-exists FAIL), then implementation (GREEN 9/9); TS plugin verified via `bun build` + `node --check` only (no opencode runtime harness in repo).

## Verification plan

- `python3 scripts/test_entry_gate_check.py` → 9/9 PASS.
- `quick_validate.py` on unified-dev-flow; backtick-ref resolver 0 unresolved.
- Install e2e in scratch dir per references/enforcement.md (never in repo); live hook install into ~/.claude/settings.json + opencode plugins is a deliberate manual step, not done by sync.

## Task: entry gate 9-tool wiring + live install

## Decisions

- enforcement.md rewritten as 9-tool manual (Claude/Codex/Cursor/Gemini/Trae/Antigravity/Kimi/Qoder/OpenCode), one checker script everywhere (stdin-JSON + exit-2 protocol is industry-converged).
- Live-installed on this machine via /tmp/install_entry_gate.py (scratch, not committed): backup-before-merge for every config, idempotent re-run verified (8 skips), existing hooks preserved (Claude Stop timeline hook, Trae danger-guard group).
- Canonical checker copy: ~/.claude/scripts/entry-gate-check.py (cross-tool ~/.claude refs already the norm here); opencode fallback copy too.
- Known per-tool caveats documented in manual: Codex apply_patch coverage intermittent (matcher has Edit|Write aliases); Gemini has no session id (SessionStart cleanup bounds staleness); Trae needs 本地自动运行 mode; Antigravity + Kimi matchers unverified-live (Beta); ZCode/Grok/PI have no public hook API (prompt-level only).

## Task: entry gate live-debug (Trae/Agy/Cursor)

## Findings

- Cursor: entry-gate PreToolUse fires (matcher Edit|Write confirmed by live block); canary removed afterwards. Done.
- Antigravity: two stacked bugs — (1) bare exit-2 fails OPEN (needs stdout {"decision":"deny"}), fixed with scripts/entry-gate-antigravity.py (also maps workspacePaths->project, conversationId->session); (2) matcher guessed wrong, canary captured real tool `write_to_file` (08:44 probe). Fixed + live-confirmed blocking. Canary removed.
- Trae: canary zero-log across absolute-path fix + full restart → hooks never execute our commands. Ruled out: bad JSON, wrong path (~/.trae-cn/hooks.json is the documented CN path; no Solo-specific path exists), matcher (Edit|Write matches Trae's real tool names per danger-guard.sh), stale config (restart done). Unresolved; user chose to stop here. entry-gate group left installed (harmless if never fired; works automatically if Trae later loads it).
- Lesson: `~` in hook commands fails open on Trae (danger-guard's absolute paths were the tell); wrong matchers fail silent everywhere — canary-first is now the standard bring-up procedure (documented in enforcement.md per-tool caveats).

## Task: Trae hook root cause (closed)

## Findings

- User confirmed BOTH stacked causes: hand-added hook group toggle was OFF in Settings > Hooks, AND run-mode was sandbox. Either alone fails silent — hence three weeks of zero logs with a 100%-correct file.
- Corrected earlier misdiagnosis ("host sovereignty"): Trae exposes full PreToolUse + deny + matcher API; the failure was entirely settings-layer. Lesson: for IDE tools, check UI toggle + run-mode BEFORE questioning the API.
- enforcement.md Trae section now records the verified two-item checklist instead of "unresolved".

## Task: entry gate bootstrap paradox (Trae field report)

## Findings

- Trae live run caught a real deadlock: writing the entry-gate artifact itself was blocked (file doesn't exist yet) — agent escaped via shell heredoc, i.e. our documented bypass became the REQUIRED path. Design miss, not a config issue.
- Fix: self-exemption — writes targeting `.omc/entry-gate-*.md` always pass (the artifact IS compliance); content validated on subsequent edits. Target read from --target, stdin tool_input path fields (file_path/filePath/path/TargetFile/…), or Codex apply_patch Update/Add File text. OpenCode plugin + Antigravity shim forward the target (thin pass-through, no logic duplication).
- TDD: 4 new cases RED first (self-write via arg/stdin narrowness apply_patch), then GREEN 13/13; live copies refreshed (installed hooks run COPIES, not repo source — easy to forget).

## Task: Phase 1 — 思维链接线（prompt only）

## Decisions

- S3 Exit += 否决记录（一行一个：否决了什么、为什么）——结构化思维的价值在没选的路，不新增技能不改表。
- Large 路线 plan 会审转正：`architect` + `plan-eng-review` 通过才进 S4（此前 architect 已有，eng-review 从备选提上来）；S3→S4 门禁同步加 large 条款。
- S8 大型/复杂迁移交付物 += `show-me-your-work` TSV 决策轨迹（思维链持久化；机械存在性检查留给 Phase 2）。
- 顺手修正 MAP 中过期的 `gstack-plan-eng-review` 旧名（与 frontmatter `plan-eng-review` 对齐；待引用解析确认）。

## Task: Phase 2 — scope 校验 + trail 检查（mechanical）

## Decisions

- Scope check on first gated edit/session (marker `.omc/.scope-ok-<session>`, re-runs when artifact edited): exists→ok, NEW:→ok, outside-project→block, missing+index→codegraph query stem (hit ok/miss block), missing+no-index→block with NEW: hint (forces explicitness, catches typos dep-free), broken CLI→warn+fail-open.
- codegraph contract probed live on scratch index: hit→JSON array, miss→`[]`, both exit 0 — so parse stdout, never trust exit code. `shutil.which` gate + 15s timeout.
- Trail check as `--check-trail` Stop-hook mode (write-gate stays write-time; end-of-work belongs to Stop): <8 edits pass, else decisions.tsv must exist+nonempty+touched-today. Snippet documented, NOT auto-installed (same manual-step rule as write gate).
- TDD: RED first (incl. fixing 2 self-inflicted test-fixture breaks from VALID edits — scope check doing its job), GREEN 26/26 incl. stub-codegraph trio (hit/miss/broken). Doc micro-template proven against real checker (caught an edit that truncated ##3/##4).

## Task: ① block 日志 + 周报（value proof）

## Decisions

- fail() 中央记账：kind（missing/malformed/scope/trail）+ session + project + reason 头 160 字，JSONL 追加，记账失败永不拦门。默认路径 ~/.claude/homunculus/entry-gate-blocks.jsonl（沿用 homunculus 惯例），ENTRY_GATE_BLOCKLOG/--block-log 可覆盖。
- scripts/entry-gate-report.py：total + 按 kind/项目/天计数 + dead-gate hint（30 天零拦截的 kind 可能是仪式）；始终 exit 0。
- TDD：5 新用例先红（含一次实现把全文件 indentation 打炸、29 红的插曲——修好后全绿，测试即安全网的实例）。

## Task: ② session-brief.py（SessionStart 记忆拼装，不造新轮子）

## Decisions

- 只读现成三层文件记忆：ck CONTEXT.md（projects.json 按 path 反查，CK_HOME 可覆盖）、项目 .omc/wiki（index + log 末 5 行）、ledger 断点、decisions.tsv 新鲜度、block 日志 7 天统计；缺失即标 无，永不崩溃永 exit 0。
- 不接 unified-memory/gbrain（前者缺 ecc-universal 运行时，后者待搭建）——等用户拍板基石方案后再看要不要第二层。
- TDD：9 断言先红后绿（含一次测试断言过细的修正）；真仓实测 graceful + 项目级 block 过滤正确。
- SessionStart 接线只写文档不装机（手动规则延续）。

## Task: MemU spike（基石验证，2026-09-07）

## Findings

- 安装坑：pip 包名是 memu-cli（裸 memu 是安卓模拟器，已卸载）；Ollama + bge-m3 本地 embedding 全程免费；本机 SOCKS 代理劫持 httpx，需 strip 代理变量（定时任务环境干净不受影响）。
- 20Q：中文转述 9.5/10（Q9 相邻半分），英译中 5/5，干扰 5 题全部有返回但分值 0.42 vs 命中 0.57+ —— 阈值 0.5 可分，调用方必须自己设阈值（memu 不拒答）。
- 适配器实测：mining 自动挖 Codex✅/Qoder-CN✅/Cursor✅，Trae-CN❌/Claude❌/Gemini/Kimi❌（方言不识别）；retrieve 通用 CLI 全工具可调。结论：inject 缝全覆盖，mining 缝按宿主分化。
- 导出：纯 SQLite 明文（memu_recall_files/segments），.dump 即全部拿回——可逆性成立，换供应商成本=重建索引。
-  verdict：GO，但范围是 recall 索引 + 手动 commit 流（贴合显式哲学），不是自动挖矿魔法。

## Decisions

- 文件永远 canonical，MemU 只做索引；session-brief.py 直读文件不受影响（逃生通道）。
- 下一步（待批）：各主力项目 AGENTS.md  patched 检索指令 + Codex/Qoder 定时挖矿任务。

## Task: xiyu×6 + nexusarchive 接 MemU 检索指令

## Decisions

- 每仓只 +7 行：长期记忆检索节（memu retrieve 一句话 + score<0.5 丢弃 + env strip 代理 + source-of-truth 声明）。xiyu 六 worktree 同文（qoder 既有差异 untouched）；nexusarchive 贴合其 §10 文档原则、无编号节改为 ## 11。
- 未在任何项目仓 commit（用户仓库用户提交）；universal-skills 侧无技能改动，仅记账。
- 当前库内 10 条为 spike 记忆（治理层内容），跨项目共享无害；生产 rollout 时按项目 commit 其 wiki/架构内容。

## Task: Review findings fix-all（P0/P1/P2）

## Decisions

- P0-1 crash 分级：exit 2 = 拦，其他非零 = 放行+警告（shim + plugin；附带修掉 bootstrap 期引入的 shim 括号残留——拖到有测试才现形，TDD 欠账的实例）。
- P0-2 scope 预算：单 query 5s + 总 6s deadline，超时 warn+跳过；10s hook 超时够用，文档不动。
- P1-1 stdin 归并（resolve_context(raw=) + read_transcript_text(raw) 共用，删 NOTE）；P1-3 _is_within 共用；P1-2 brief/report 尾读（3000/20000 行 cap）。
- P2：TEMPLATE_HINT 补 NEW: 半句；SessionStart 清理 glob 扩 .scope-ok-*；--block-log 改模块变量（去 env mutation）；trail 一日语义文档承认；tests 随 sync 发布问题：sync 全目录 symlink 改排除面太大，决议接受现状（单技能测试 ~10KB，概念瑕疵换零风险），有异议可推翻。
- 环境插曲：本机 python3 切到 Homebrew 3.14（无 yaml），quick_validate 改用 miniconda python 跑；自研脚本 stdlib-only 故免疫——当初立的规矩兑现了。

## Task: P0 三件套（多轮 Review Fix Loop + 对抗测试门 + 简洁机械化，2026-09-08）

## Findings

- S6 是单遍评审：`interrogate` 一次性、无收敛条件、无回路；reviewer 可直接改代码（无 judge 约束），作者自审盲区仍在。业界基线（2026 多智能体综述）：reviewer 只判不改 + fix loop + 同轮超 3 次 ESCALATE（多半是 spec 模糊，回 S2 不换 agent 硬试）。
- S5 无对抗测试：`interrogate` 是对抗性审查不是对抗性测试；`self-verifying-tests`/`ultraqa` 躺在备选；2026 PROBE/AdverTest 论文证明 mutation-guided 双智能体循环 +9.79% mutation / +8.56% FDR。
- 简洁性纯 prompt：`ai-slop-cleaner` 无度量；仓内已有 `health`（0–10 综合分，包 lint/type/tests/dead code）未被 router 使用。

## Decisions

- S6 三步变强制链：`ai-slop-cleaner` → `health`（相对改前基线下降即拦，不设绝对分绝对值——项目自定 floor）→ `google-code-review`；fix loop 裁决 MERGE_READY/NEEDS_FIXES，max 3 次 S4 修复后 ESCALATE 由人定夺，feedback 文档为唯一输入增量。
- S5 新增对抗分支：auth/数据/安全路径强制、其余推荐——`self-verifying-tests` 跨层 + diff 级 mutation 全杀（有项目 runner 用 runner，无则 reviewer 手写 counter-cases）；存活 mutant = NEEDS_FIXES 进 S6 循环。
- alternatives.md 同步：S5 把 `self-verifying-tests` 标为已转正、保留 `ultraqa` 作 loop 引擎（S6 内 cap 3 次非原生 5 次）；S6 标注 `health` 已转正、`codehealth-mcp` 留作 MCP 版备选。
- WORKFLOW-MAP.md §二 S5/S6 + 门禁规则同步跟进（SKILL↔MAP 曾经发散过，本次成对改）。
- DEVIATION 预告：health 基线对比需要改前跑一次分（S4 前或 S6 开头），多一次工具调用；若实战证明噪音大，退回仅记录不拦门。

## Verification plan

- miniconda python 跑 `quick_validate.py` → valid（本机 brew python3 无 yaml，老问题）。
- backtick 引用解析 139 个：新增 `health`/`self-verifying-tests`/`codehealth-mcp`/`ultraqa` 全部单命中；`speckit-*` 未命中是自查脚本对引号 frontmatter 的误报（pre-existing 引用，线上正常）。

## Task: P2 收尾（skillify 清理 + standard-workflow 双向引用 + entry-gate 小修，2026-09-08）

## Findings

- gstack/skillify/ 下有一个指向 imported/skillify 的同名 symlink（skillify → imported/skillify），两者 frontmatter name 不同（skillify vs omc-skillify），非重名冲突但易误导。
- standard-workflow 只单向引用 unified-dev-flow（轻量 4 阶段），反向无导航。
- entry-gate: TEMPLATE_HINT 已含 NEW: 提示；block-log 已模块变量化（_block_log_override）；SessionStart 缺 .scope-ok-* 清理。

## Decisions

1. **skillify symlink 清理 + 文档**：删除 gstack/skillify/skillify symlink；在 SKILL.md "When to invoke" 追加说明区分 gstack/skillify（/scrape 固化）vs imported/omc-skillify（workflow→OMC skill 草稿）。
2. **standard-workflow 双向引用**：概览段落追加 "需要更完整的 9 阶段流程？参见 unified-dev-flow..."。
3. **entry-gate SessionStart 清理**：session-brief.py main() 开头加清理 .scope-ok-* 陈旧标记（无痕、不阻塞）。

## Tradeoffs

- gstack/skillify 的 `triggers`、`version` frontmatter 超出 quick_validate 允许列表（pre-existing，不改动以保 upstream 兼容）。
- gstack/* 与 imported/gstack/* 镜像导致的重复引用非本次引入，不再处理。

## Verification plan

- quick_validate：unified-dev-flow / standard-workflow → valid；gstack/skillify 仅 warning（前缀键，非错误）。
- 引用解析 143 个：新增 `unified-dev-flow` 反向引用单命中；其余重复为 pre-existing 镜像。

## Task: trail Stop 无限循环保险

## Findings

- S2 无章程约束：`speckit-constitution` 躺在 imported，中型以上没人用；Entry Gate §1 已读约束文档（RULES/lessons-learned/AGENTS）未被规范化为章程。ETH 2026 实验证实：LLM 生成的 AGENTS.md 无益甚至 -3% 成功率，开发者自写的 constitution 提供 +4% 提升。
- S6 同模型自审盲区：`interrogate` 读 `pstack-models.mdc` 但 router 未强制异 lab；业界 2026 多智能体综述共识——同 family 模型共享 failure surface，跨 vendor 评审必需。
- MemU mining 仅止于 spike：Codex/Qoder 已有专用 adapter 且 memorization works（detect 确认），但无定时任务、各仓无检索指令；Claude/Trae/Gemini/Kimi 需专用 adapter 或方言支持。

## Decisions

1. **constitution 必选化（中型以上）**：
   - S2 spec 阶段：必须声明章程来源——`.specify/` 存在则 `speckit-constitution`，否则 Entry Gate §1 读到的约束文档作章程
   - S3 exit 新增门禁：plan 无 constitution 违规，或豁免列表已列出
   - alternatives.md 同步：speckit-constitution 标为 medium+ mandatory

2. **跨模型评审路由**：
   - S6 新增 cross-model gate：reviewer 与 implementer 异 lab（`PSTACK_REVIEW_MODELS` 或 `~/.config/opencode/skills/pstack-models.mdc` 指定）；未配置退化为同模型强制 `interrogate`
   - reviewer 只判不改（judge pattern）已在 P0 确立
   - alternatives.md 同步：S6 备选表新增 cross-model gate 条目

3. **MemU 挖矿 rollout（Codex/Qoder 定时 + 各仓检索指令）**：
   - memory-backend.md 新增 Rollout 章节：AGENTS.md 统一追加检索指令（`memu-agent retrieve --score 0.5` + 代理 strip 前缀）+ Codex/Qoder launchd plist（每天 03:00/03:15 prepare，周一手动 commit）
   - 验收标准 4 条：doctor 绿、AGENTS.md 命中、plist loaded 有输出、retrieve 命中非空
   - Trae/Gemini/Kimi/Claude 待 adapter/dialect 支持，暂不阻塞 rollout

## Tradeoffs / DEVIATIONS

- constitution 豁免列表由人维护（不自动），避免误判锁死；若实战噪音大可改为 warn-only
- cross-model 退化同模型 `interrogate` 仍保底——不阻塞流程，只是少了一层异构防御
- MemU mining 仅覆盖 Codex/Qoder（adapter ready + memorization works），其他工具等上游 adapter；不影响检索（retrieve CLI 通用）

## Verification plan

- `quick_validate.py` → valid（miniconda python，brew python3 无 yaml 老问题）
- backtick 引用解析 141 个：新增 `speckit-constitution`/`PSTACK_REVIEW_MODELS`/cross-model 全部单命中；gstack/* 重复是 imported 镜像导致的 pre-existing duplication，非本次引入

## Task: trail Stop 无限循环保险

## Decisions

- --max-blocks（默认 3）：同 episode 拦超 3 次转大声放行（stderr + trail-giveup 记账），计数器按 session 存 .omc、通过/放行即清零，下回重装。
- 附带修真 bug：trail 模式 stdin 被读两次（--transcript 缺省时 transcript 恒空→恒过）；现单读一次透传。旧测试没抓到是因为全传 --transcript 文件——新增 stdin 形态用例锁住。

## Task: Stop 接线三家（agy/opencode/zcode）

## Decisions

- Agy Stop 全支持：shim --stop（exit2→continue/0→stop/其他→stop+warn；transcriptPath 驼峰显式透传）。诊断插曲：e2e 误放行查到是线上拷贝滞后（repo 已改、~/.claude 未重拷）——再次证明"线上跑的是拷贝"这条运维铁律，修后 e2e 双态全绿。
- checker 编辑计数泛化：EDIT_TOOL_PATTERN 覆盖 agy 三工具名（transcript 实测取样）；Claude 系行为不变（回归测试锁）。
- OpenCode 无可阻塞 stop 事件 → session.idle 提醒器（计数≥8、每会话一次、toast+log），human-in-loop，明示 warn-only。
- ZCode 无 hook API（cli/config.json 仅 plugins+mcp；v2/setting.json 无 hook 键）→ prompt 版 only。附带发现其 MCP 已有 everme 记忆 + sequential-thinking，记入记忆 rollout。
