---
name: unified-dev-flow
description: 当开始非简单的功能开发、修 bug、重构或迁移，需要决定走哪些阶段、调用哪些技能、走多深时使用。当用户问该用什么流程或技能时使用。触发词：统一流程 / 标准流程 / 开发流程 / 完整流程 / 走流程 / 端到端开发 / 该用什么技能 / 帮我选流程 / 怎么推进这个需求 / 规范流程。Use when deciding which dev workflow/skills to use for a non-trivial coding task.
---

# Unified Dev Flow

## Overview

A **thin router**: selects and chains existing skills by name, never re-implements them.
Alternatives and domain-specialist tables live in `references/alternatives.md`
(load on demand, never by default). `WORKFLOW-MAP.md` at the repo root is the
design doc behind this router — it is not installed with the skill.

1. **Gates before stages** — a failed gate stops progression until resolved.
2. **Scale decides depth** — classify FIRST; only large tasks walk all 9 stages.

## Entry Gate (mandatory first output)

Before classifying or loading any stage skill, emit these 4 items. Missing any one = STOP.
Each item feeds exactly one downstream gate — instantiate it for THIS task,
never restate the rule (don't write "我将遵循 TDD"; write
"失败测试：`tests/x_test.py::test_y`；验证命令：`pytest tests/x_test.py`"):

1. **理解和假设** → S1/S2: restate the problem in your own words, list uncertain
   assumptions, and name the project constraint docs read (`RULES.md` /
   `lessons-learned.md` / `AGENTS.md`, if present).
2. **最小方案 + 文件范围** → S3: what changes and where (file list, new files prefixed `NEW:`); no code yet.
3. **范围纪律** → S6: only directly-related code; side findings noted, never touched.
4. **验证计划** → S5: failing test first + the exact commands whose output will prove it.

First `Edit`/`Write` is mechanically gated (see `references/enforcement.md`):
no well-formed `.omc/entry-gate-<sessionID>.md` on disk = tool call blocked.
Micro-change writes the same 4 headers, one line each — no size exemption.

## Step 1 — Classify the task

| Task type | Telltale signs | Route |
|---|---|---|
| 微改动 Micro-change | Single file, <50 lines, behavior clear | S4 direct → S5 (skip S0–S3) |
| Bug 修复 Bug fix | Reproducible failure, regression | S0 → debug chain → S4 (failing test first) → S5 → S6 (light) → S7 |
| 纯重构 Refactor | Behavior-preserving, tech debt, modularity | S0 → S3 (`writing-plans`) → S4 (refactor + regression tests) → S5 → S6 → S7 |
| 调研探路 Research/Spike | Tech evaluation, feasibility PoC, no ship | S1 → S3 (`research` / `prototype`) → S8 (file memo, stop) |
| 小需求 Small feature | 1–3 files, clear scope | S0 → S4 (TDD) → S5 → S6 (light) → S7 |
| 中型需求 Medium feature | Multi-module, needs step breakdown | S0 → `speckit-chain`（constitution→specify→plan→tasks→implement 全链）→ S5 → S6 → S7 |
| 大型特性 Large feature | Cross-layer, high risk, vague requirements | S0 → `speckit-chain`（S1–S4，plan 追加 `architect` 会审 + `plan-eng-review`，多视角通过才进 S4）→ S5 → S6 → S7 → S8；追加门禁：`interrogate` + `production-risk-review` |
| 复杂迁移 Intractable | Multi-week, needs audit trail | `figure-it-out` playbook mode |

## When NOT to use

- Trivial fix one skill covers (typo, rename, one-liner) — just do it.
- Pure domain action with no code change (e.g. "make a PDF", "search docs") — route to domain specialist directly.
- Already mid-flight in a structured flow (`speckit-chain`, active plan file) — finish it.
- User named the exact workflow they want (e.g. 标讯项目点名 `blueprint-driven-development`).
- User explicitly wants the lighter omc 4-phase flow (`standard-workflow`) — don't intercept.

## Step 2 — Walk only your route's stages

Load stage skills for your route, plus any domain specialist (see Cross-cutting):

| Stage | Question | Canonical skill | Exit when |
|---|---|---|---|
| S0 Prepare | Isolated workspace? Unfinished prior run? | 先查 `.superpowers/sdd/progress.md`：有未完成 ledger 则续跑、不重新分级；否则 `using-git-worktrees`（resume: `recall`）；首次 Edit/Write 由 entry-gate hook 机械拦截 | Workspace ready, breakpoint resumed or fresh |
| S1 Intent | Why do this? | `brainstorming`; PRD: `parse-prd`; product analysis: `product-analysis`; domain terms: `domain-modeling` | User confirms scope |
| S2 Spec | What exactly? | `speckit-specify` → `speckit-clarify`; light path: `to-spec` | Spec written & ambiguity resolved |
| S3 Plan | How, in what order? | `writing-plans`; architecture-first: `architect`; design validation: `prototype`; schema/query: `access-pattern-driven-data-modeling`; heavy path: `speckit-plan` → `speckit-tasks` | Plan with verification points + rejected alternatives (one line each: dropped, why) |
| S4 Implement | Build it | `test-driven-development` via `subagent-driven-development` (fallback: `executing-plans`; unattended: `autopilot` / `ralph`; convergence: `speckit-converge`; DB scripts: `create-migration`) | Code + tests per plan |
| S5 Verify | Prove it works | `verification-before-completion` (+ `principle-prove-it-works`); E2E: `e2e-testing` | Real command evidence |
| S6 Review | Find flaws | `ai-slop-cleaner` → `google-code-review` (mandatory, see Gates); spec-bearing routes add `code-review` for spec consistency; medium+ ends with `interrogate`; optional: live/prod `production-risk-review`, security `security-review`, impact `blast-radius`, architecture `architecture-defense` | Gates S6 conditions met, findings addressed |
| S7 Ship | Integrate & deploy | `finishing-a-development-branch` → `ship`; unattended (`autopilot`/`ralph`): `ai-release-engineer`; migrations: `database-migrations`; deploy infra: `deployment-patterns`; post-deploy: `canary` | Merged, deployed |
| S8 Capture | Get smarter | `knowledge-capture` (auto: `continuous-learning-v2`; review: `reflect`); large/intractable 追加 `show-me-your-work` 决策轨迹 | Knowledge filed (+ decision trail for large/intractable) |

Large-feature one-shot: `speckit-chain`.

## Gates (hard stops)

- **Entry → Step 1**: 4-item statement missing = STOP. First `Edit`/`Write` is
  mechanically blocked until `.omc/entry-gate-<sessionID>.md` exists and is
  well-formed (see `references/enforcement.md`).
- **S1 → S2**: unclear intent blocks spec writing — clarify first.
- **S3 → S4**: no written plan, no code — micro-change and small-feature fast paths exempt; S5 verification never exempt; large: plan review (`architect` + `plan-eng-review`) must pass.
- **S5 → S6**: completion claims need real command evidence, not "it compiles".
- **S6 进入即强制**：所有走到 S6 的路线（含 light）都必须过 `ai-slop-cleaner` + `google-code-review`，缺一不可跳过；有 spec 的路线加 `code-review` 做 spec 一致性。
- **S6 收尾（中型及以上）**：评审通过后还需 `interrogate` 对抗性审查；light 路径（微改动/Bug/小需求）可选。
- **S6 → S7 (production)**: PRs touching a live system MUST pass `production-risk-review`.
- **S6 → S7 (unattended AI)**: `autopilot` / `ralph` 全自主产出必须过 `ai-release-engineer` gates；日常结对路线以 S7 `ship` 为准，不重复设卡。

## Cross-cutting (enter at any stage)

- **Domain specialists** (load alongside any route; pure non-code tasks run them alone): UI → `frontend-design` / `ui-ux-pro-max`; perf → `performance-tuning`; refactor → `clean-code-behavior-preserving-refactoring` / `entropy-reduction`; research → `research`; docs → `technical-writing` / `html-first-workflow`; API → `api-design`.
- **Debug escalation**: `systematic-debugging` → `root-cause-hunter` → `paranoid-debugging`.
- **Parallel dispatch** (subtasks strictly independent, no shared state): `dispatching-parallel-agents` for task fan-out; `team` for a shared task list; `swarm` for N workers, one report.
- **Deep requirements**: `deep-interview` / `deep-dive` when S1 intent is highly ambiguous.
- **Context & principles**: `strategic-compact`, `context-save`/`context-restore`; standing principles `principle-prove-it-works`, `principle-fix-root-causes`, `principle-sequence-verifiable-units`, `principle-guard-the-context-window`; remaining `principle-*` load on demand.

## Common mistakes

- Walking all 9 stages manually for a medium+ task — 中型及以上直接 `speckit-chain`，不要手工拆 S1–S4。
- Re-classifying over an unfinished `.superpowers/sdd/` ledger instead of resuming it.
- Skipping the S6 mandatory reviewers (`ai-slop-cleaner` / `google-code-review`) under time pressure; a waived gate must be explicit with the user.
- Declaring work complete on "it compiles" without running real verification.
- Forgetting to scan domain cross-cutting signals after scale classification.
- Copying skill bodies into plans — reference by name, load on demand.
