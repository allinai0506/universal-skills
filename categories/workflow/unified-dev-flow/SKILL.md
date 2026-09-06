---
name: unified-dev-flow
description: 当开始非简单的功能开发、修 bug、重构或迁移，需要决定走哪些阶段、调用哪些技能、走多深时使用。当用户问该用什么流程或技能时使用。触发词：统一流程 / 标准流程 / 开发流程 / 完整流程 / 走流程 / 端到端开发 / 该用什么技能 / 帮我选流程 / 怎么推进这个需求 / 规范流程。
---

# Unified Dev Flow

## Overview

A **thin router**: selects and chains existing skills by name, never re-implements them.
Complete catalog and alternatives live in `WORKFLOW-MAP.md` at the repo root.

1. **Gates before stages** — a failed gate stops progression until resolved.
2. **Scale decides depth** — classify FIRST; only large tasks walk all 9 stages.

## Step 1 — Classify the task

| Task type | Telltale signs | Route |
|---|---|---|
| 微改动 Micro-change | Single file, <50 lines, behavior clear | S4 direct → S5 (skip S0–S3) |
| Bug 修复 Bug fix | Reproducible failure, regression | S0 → debug chain → S4 (failing test first) → S5 → S6 (light) → S7 |
| 纯重构 Refactor | Behavior-preserving, tech debt, modularity | S0 → S3 (`writing-plans`) → S4 (refactor + regression tests) → S5 → S6 → S7 |
| 调研探路 Research/Spike | Tech evaluation, feasibility PoC, no ship | S1 → S3 (`research` / `prototype`) → S8 (file memo, stop) |
| 小需求 Small feature | 1–3 files, clear scope | S0 → S4 (TDD) → S5 → S6 (light) → S7 |
| 中型需求 Medium feature | Multi-module, needs step breakdown | S0 → `speckit-chain`（constitution→specify→plan→tasks→implement 全链）→ S5 → S6 → S7 |
| 大型特性 Large feature | Cross-layer, high risk, vague requirements | S0 → `speckit-chain` + 追加门禁：`architect` plan review + `interrogate` + `production-risk-review` + `ship` → S8 |
| 复杂迁移 Intractable | Multi-week, needs audit trail | `figure-it-out` or `blueprint-driven-development` playbook mode |

## When NOT to use

- Trivial fix one skill covers (typo, rename, one-liner) — just do it.
- Pure domain action with no code change (e.g. "make a PDF", "search docs") — route to domain specialist directly.
- Already mid-flight in a structured flow (`speckit-chain`, active plan file) — finish it.
- User named the exact workflow they want.

## Step 2 — Walk only your route's stages

Load stage skills for your route, plus any domain specialist (see Cross-cutting):

| Stage | Question | Canonical skill | Exit when |
|---|---|---|---|
| S0 Prepare | Isolated workspace? | `using-git-worktrees` (resume: `recall`) | Workspace ready |
| S1 Intent | Why do this? | `brainstorming`; PRD: `parse-prd`; product analysis: `product-analysis`; domain terms: `domain-modeling` | User confirms scope |
| S2 Spec | What exactly? | `speckit-specify` → `speckit-clarify`; light path: `to-spec` | Spec written & ambiguity resolved |
| S3 Plan | How, in what order? | `writing-plans`; architecture-first: `architect`; design validation: `prototype`; schema/query: `access-pattern-driven-data-modeling`; heavy path: `speckit-plan` → `speckit-tasks` | Plan with verification points |
| S4 Implement | Build it | `test-driven-development` via `subagent-driven-development` (fallback: `executing-plans`; unattended: `autopilot` / `ralph`; convergence: `speckit-converge`; DB scripts: `create-migration`) | Code + tests per plan |
| S5 Verify | Prove it works | `verification-before-completion` (+ `principle-prove-it-works`); E2E: `e2e-testing` | Real command evidence |
| S6 Review | Find flaws | **强制两步**：先 `ai-slop-cleaner` 清 slop，再 `google-code-review` 正式评审；**中型及以上最后必过 `interrogate` 对抗性审查收尾**（light 路径可选）；可选加: live/prod: `production-risk-review`; security: `security-review`; impact: `blast-radius`; architecture: `architecture-defense` | 两个强制 pass 完成且 findings addressed；中型及以上另需 `interrogate` 完成 |
| S7 Ship | Integrate & deploy | `finishing-a-development-branch` → `ship`; AI-authored: `ai-release-engineer`; migrations: `database-migrations`; deploy infra: `deployment-patterns`; post-deploy: `canary` | Merged, deployed |
| S8 Capture | Get smarter | `knowledge-capture` (auto: `continuous-learning-v2`; review: `reflect`) | Knowledge filed |

Large-feature one-shot: `speckit-chain`.

## Gates (hard stops)

- **S1 → S2**: unclear intent blocks spec writing — clarify first.
- **S3 → S4**: no written plan, no code — micro-change fast path exempt.
- **S5 → S6**: completion claims need real command evidence, not "it compiles".
- **S6 进入即强制**：所有走到 S6 的路线（含 light）都必须过 `ai-slop-cleaner` + `google-code-review`，缺一不可跳过。
- **S6 收尾（中型及以上）**：双审通过后还需 `interrogate` 对抗性审查；light 路径（微改动/Bug/小需求）可选。
- **S6 → S7 (production)**: PRs touching a live system MUST pass `production-risk-review`.
- **S6 → S7 (AI-authored)**: AI-generated code MUST pass `ai-release-engineer` gates; failure = STOP.

## Cross-cutting (enter at any stage)

- **Domain specialists** (load alongside any route; pure non-code tasks run them alone): UI → `frontend-design` / `ui-ux-pro-max`; perf → `performance-tuning`; refactor → `clean-code-behavior-preserving-refactoring` / `entropy-reduction`; research → `research`; docs → `technical-writing` / `html-first-workflow`; API → `api-design`.
- **Debug escalation**: `systematic-debugging` → `root-cause-hunter` → `paranoid-debugging`.
- **Data modeling & query perf**: `access-pattern-driven-data-modeling` for tables, indexes, queries, denormalization.
- **Parallel dispatch**: `dispatching-parallel-agents` / `team` / `swarm` when subtasks are strictly independent.
- **Deep requirements**: `deep-interview` / `deep-dive` when S1 intent is highly ambiguous.
- **Context & principles**: `principle-guard-the-context-window`, `strategic-compact`, `context-save`/`context-restore`; pstack `principle-*` constrain every stage.

## Common mistakes

- Walking all 9 stages manually for a medium+ task — 中型及以上直接 `speckit-chain`，不要手工拆 S1–S4。
- Skipping the S6 mandatory reviewers (`ai-slop-cleaner` / `google-code-review`) under time pressure; a waived gate must be explicit with the user.
- Declaring work complete on "it compiles" without running real verification.
- Forgetting to scan domain cross-cutting signals after scale classification.
- Copying skill bodies into plans — reference by name, load on demand.
