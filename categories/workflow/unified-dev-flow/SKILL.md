---
name: unified-dev-flow
description: Use when starting a non-trivial feature, bugfix, refactor, or migration and need to decide which stages and skills apply at what depth; when the user asks which workflow or skills to follow; or says 统一流程 / 完整流程 / 走流程.
---

# Unified Dev Flow

## Overview

A **thin router**: it selects and chains existing skills — it never re-implements them.
Each stage names one canonical skill to load for that phase. Alternatives live in
`WORKFLOW-MAP.md` at the universal-skills repo root.

Two rules govern every route:

1. **Gates before stages.** A gate that fails stops progression until resolved (see Gates).
2. **Scale decides depth.** Classify the task FIRST — most tasks skip several stages; only large ones walk all 9.

## Step 1 — Classify the task

| Task type | Telltale signs | Route |
|---|---|---|
| Micro-change | Single file, <50 lines, behavior clear | S4 direct → S5 (skip S0–S3) |
| Bug fix | Reproducible failure | S0 → debug chain → S4 (failing test first) → S5 → S7 |
| Small feature | 1–3 files | S0 → S4 (TDD) → S5 → S6 (light) → S7 |
| Medium feature | Multi-module, needs breakdown | S0 → S1 → S3 (`writing-plans`) → S4 (`subagent-driven-development`) → S5-S7 |
| Large feature / new system | Cross-layer, high risk, vague requirements | Full flow S0→S8 with speckit spec + `architect` plan review + `interrogate` + `production-risk-review` + `ship` |
| Intractable / big migration | Multi-week, needs audit trail | `figure-it-out` or `blueprint-driven-development` playbook mode |

## When NOT to use this skill

- Trivial fix one skill already covers (typo, rename, one-line tweak) — just do it.
- Already mid-flight in a structured flow (`speckit-chain`, active plan file) — finish that; don't re-route.
- The user explicitly named the workflow they want.

## Step 2 — Walk only the stages your route includes

Load only the canonical skill per stage you actually enter:

| Stage | Question | Canonical skill | Exit condition |
|---|---|---|---|
| S0 Prepare | Isolated workspace? | `using-git-worktrees` (resume work: `recall`) | Worktree/session ready |
| S1 Intent | Why do this? | `brainstorming` | User confirms intent & scope |
| S2 Spec | What exactly? | `speckit-specify` → `speckit-clarify`; light path: `to-spec` | Written spec, ambiguities resolved |
| S3 Plan | How, in what order? | `writing-plans`; architecture-first: `architect`; schema/index/query-path changes: `access-pattern-driven-data-modeling` | Plan with verification points |
| S4 Implement | Build it | `test-driven-development` loop via `subagent-driven-development` (fallback: `executing-plans`) | Code + tests per plan |
| S5 Verify | Prove it works | `verification-before-completion` (+ `principle-prove-it-works`) | Real command output as evidence |
| S6 Review | Find flaws | `code-review`; adversarial: `interrogate`; security: `security-review` | Findings addressed |
| S7 Ship | Integrate & deploy | `finishing-a-development-branch` → `ship`; post-deploy: `canary` | Merged, versioned, PR opened |
| S8 Capture | Get smarter | `knowledge-capture` | Reusable knowledge filed |

One-shot alternative for large features: `speckit-chain`.

## Gates (hard stops)

- **S1 → S2**: unclear intent blocks spec writing — clarify first.
- **S3 → S4**: no written plan, no code — except the micro-change fast path.
- **S4 → S5**: completion claims require real verification evidence (ran commands, saw output).
- **S5 → S7**: PRs touching a live/production system MUST pass `production-risk-review` instead of a plain code review.

## Cross-cutting (enter at any stage)

- **Debugging escalation**: `systematic-debugging` → `root-cause-hunter` → `paranoid-debugging`.
- **Data modeling & query performance**: `access-pattern-driven-data-modeling` when work touches tables, indexes, list/search/report queries, denormalization/read models, or data-access perf (e.g. slow query found at S5).
- **Context management**: `principle-guard-the-context-window` (route bulk to subagents), `strategic-compact` (compress at milestones), `context-save`/`context-restore` (across sessions).
- **Principles layer**: pstack `principle-*` skills constrain every stage (e.g. `principle-subtract-before-you-add`, `principle-fix-root-causes`, `principle-sequence-verifiable-units`).

## Common mistakes

- Walking all 9 stages for a small/medium task. Classification decides the route — re-check Step 1 before entering any stage.
- Skipping gates under time pressure. A waived gate must be explicit with the user.
- Copying skill bodies into plans or prompts. Reference by name, load on demand; default to canonical skills, switch to `WORKFLOW-MAP.md` alternatives only when their stated condition applies.
