# unified-dev-flow — Alternatives & Domain Tables

On-demand reference for the `unified-dev-flow` router. The canonical
stage→skill mapping lives in `SKILL.md`; this file only lists **alternatives
and specialist tables** that were compressed out of the main file.
Load this file only when the canonical skill doesn't fit — never by default.

Design rationale lives in `WORKFLOW-MAP.md` at the repo root (repo checkout
only, not installed with the skill).

## Stage alternatives (replace canonical only when the condition hits)

- S0: `project-session-manager` (multi-ticket parallel worktrees);
  `recall` (resume prior work); `deepinit` (first entry into a new codebase).
- S1: `grill-with-docs` (need ADR + glossary as you go);
  `deep-interview` (extreme ambiguity, Socratic probing).
- S2: `spec` (output is issues/tickets for GitHub flow);
  `speckit-constitution` (one-time project charter, **medium+ mandatory** —
  no `.specify/` → Entry Gate §1 constraint docs act as constitution);
  `domain-modeling` (ubiquitous language).
- S3: `speckit-plan` + `speckit-tasks` (heavy doc pipeline);
  `plan-eng-review` / `plan-ceo-review` / `plan-design-review`
  (large/high-risk multi-view review); `speckit-analyze` / `speckit-checklist`
  (spec-plan-tasks consistency); `arena` / `principle-exhaust-the-design-space`
  (no-precedent design, prototype 2–3 first).
- S4: `implement` (spec/tickets exist, small-medium build);
  `executing-plans` (no-subagent env); `autopilot` / `ralph` +
  `show-me-your-work` (unattended long runs).
- S5: `self-verifying-tests` is now a canonical adversarial branch (see SKILL.md),
  not an alternative; remaining alts: `ultraqa` (fix-loop engine — cap at 3
  cycles inside the S6 loop, not its native 5); `create-verification-skill` +
  `maintain-verification-skill` (project-level verify);
  language rigs (`cpp-testing`, etc.).
- S6: `cog-4d-audit` (CI-green but uneasy); `health` is now canonical
  (see SKILL.md S6), `codehealth-mcp` stays the alt when a live structural
  score via MCP is preferred over the CLI dashboard; `blast-radius` before the change
  (impact); `cso` (OWASP + threat model); `qa` (fix) / `qa-only` (report
  only); `receiving-code-review` (when being reviewed: verify feedback,
  don't blindly obey); **cross-model gate** — reviewer from different lab
  than implementer (env `PSTACK_REVIEW_MODELS` or `~/.config/opencode/skills/pstack-models.mdc`,
  missing → same-model `interrogate` fallback).
- S7: `release` (repo-rule-driven release); `deployment-patterns` /
  `docker-patterns` / `database-migrations` / project deploys
  (e.g. `xiyu-server-deploy`).
- S8: `continuous-learning-v2` (auto distill); `retro` (periodic review);
  `learner` / `automate-me` (freeze success into a skill).

## Domain specialists (full table)

| 领域信号 | 首选 | 备选/说明 |
|---|---|---|
| UI 构建/打磨 | `frontend-design` | `ui-ux-pro-max`（BM25：50+ 风格 / 97 色板 / 57 字体 / 99 UX 准则） |
| CPU/内存/GC/锁、慢接口 | `performance-tuning` | 数据访问慢查询走 `access-pattern-driven-data-modeling` 验证环节（EXPLAIN + 访问模式对照） |
| 行为保持重构 | `clean-code-behavior-preserving-refactoring` | `entropy-reduction`（模块边界、循环依赖） |
| 调研/选型 | `research`（一手资料 → Markdown） | `search-first`（写码前找轮子） |
| 正式文档/交付 | `html-first-workflow` | `technical-writing` / `make-pdf` |
| API 设计/改造 | `api-design` | — |
| DB 方言专项 | `postgres-patterns` / `clickhouse-io` | 按栈选用 |

## Debug escalation (full)

`systematic-debugging` (entry) → `root-cause-hunter` (prove root cause) →
`paranoid-debugging` (prod-critical evidence pass).
Others: `diagnosing-bugs` (HITL loop), `trace` (competing hypotheses),
`deep-dive`, `investigate`.
