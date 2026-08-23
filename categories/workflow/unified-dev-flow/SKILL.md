---
name: unified-dev-flow
description: Use when starting a non-trivial feature, bugfix, refactor, or migration and need to decide which stages and skills apply at what depth; when the user asks which workflow or skills to follow; or says 统一流程 / 完整流程 / 走流程.
---

# Unified Dev Flow

## Overview

A **thin router**: selects and chains existing skills by name, never re-implements them.
Alternatives live in `WORKFLOW-MAP.md` at the repo root.

1. **Gates before stages** — a failed gate stops progression until resolved.
2. **Scale decides depth** — classify FIRST; only large tasks walk all 9 stages.

## Step 1 — Classify the task

| Task type | Telltale signs | Route |
|---|---|---|
| Micro-change | Single file, <50 lines, behavior clear | S4 direct → S5 (skip S0–S3) |
| Bug fix | Reproducible failure | S0 → debug chain → S4 (failing test first) → S5 → S7 |
| Small feature | 1–3 files | S0 → S4 (TDD) → S5 → S6 (light) → S7 |
| Medium feature | Multi-module, needs breakdown | S0 → S1 → S3 (`writing-plans`) → S4 (`subagent-driven-development`) → S5-S7 |
| Large feature / new system | Cross-layer, high risk, vague requirements | Full flow S0→S8 with speckit spec + `architect` plan review + `interrogate` + `production-risk-review` + `ship` |
| Intractable / big migration | Multi-week, needs audit trail | `figure-it-out` or `blueprint-driven-development` playbook mode |

## When NOT to use

- Trivial fix one skill covers (typo, rename, one-liner) — just do it.
- Already mid-flight in a structured flow (`speckit-chain`, active plan file) — finish it.
- User named the workflow they want.

## Step 2 — Walk only your route's stages

Load stage skills for your route, plus any domain specialist (see Cross-cutting):

| Stage | Question | Canonical skill | Exit when |
|---|---|---|---|
| S0 Prepare | Isolated workspace? | `using-git-worktrees` (resume: `recall`) | Workspace ready |
| S1 Intent | Why do this? | `brainstorming` | User confirms scope |
| S2 Spec | What exactly? | `speckit-specify` → `speckit-clarify`; light path: `to-spec` | Spec written |
| S3 Plan | How, in what order? | `writing-plans`; architecture-first: `architect`; schema/index/query-path changes: `access-pattern-driven-data-modeling` | Plan with verification points |
| S4 Implement | Build it | `test-driven-development` via `subagent-driven-development` (fallback: `executing-plans`) | Code + tests per plan |
| S5 Verify | Prove it works | `verification-before-completion` (+ `principle-prove-it-works`) | Real command evidence |
| S6 Review | Find flaws | `code-review`; adversarial: `interrogate`; security: `security-review` | Findings addressed |
| S7 Ship | Integrate & deploy | `finishing-a-development-branch` → `ship`; AI-authored code: `ai-release-engineer`; post-deploy: `canary` | Merged, PR opened |
| S8 Capture | Get smarter | `knowledge-capture` | Knowledge filed |

Large-feature one-shot: `speckit-chain`.

## Gates (hard stops)

- **S1 → S2**: unclear intent blocks spec writing — clarify first.
- **S3 → S4**: no written plan, no code — micro-change fast path exempt.
- **S4 → S5**: completion claims need real command evidence.
- **S5 → S7**: PRs touching a live/production system MUST pass `production-risk-review` instead of a plain code review.
- **S5 → S7 (AI-authored release)**: AI-generated changes MUST pass `ai-release-engineer` gates before merge or production promotion; failure = STOP.

## Cross-cutting (enter at any stage)

- **Domain specialists** (load alongside any route; pure non-code tasks run them alone): UI build/polish → `frontend-design` / `ui-ux-pro-max`; CPU/memory/lock perf → `performance-tuning`; behavior-preserving refactor → `clean-code-behavior-preserving-refactoring` / `entropy-reduction`; research/selection → `research`; customer-facing docs → `technical-writing` / `html-first-workflow`.
- **Debug escalation**: `systematic-debugging` → `root-cause-hunter` → `paranoid-debugging`.
- **Data modeling & query perf**: `access-pattern-driven-data-modeling` for tables, indexes, list/search/report queries, denormalization/read models, slow-query diagnosis.
- **Context**: `principle-guard-the-context-window`, `strategic-compact`, `context-save`/`context-restore`.
- **Principles**: pstack `principle-*` constrain every stage (e.g. subtract-before-you-add, fix-root-causes).

## Common mistakes

- Walking all 9 stages for a small/medium task — re-check Step 1 first.
- Skipping gates under time pressure; a waived gate must be explicit with the user.
- Copying skill bodies into plans — reference by name, load on demand; switch to `WORKFLOW-MAP.md` alternatives only when their stated condition applies.
