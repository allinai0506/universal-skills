# unified-dev-flow — Alternatives & Domain Tables

On-demand reference for the `unified-dev-flow` router. The canonical
stage→skill mapping lives in `SKILL.md`; this file only lists **conditional
stage selections and specialist tables** that were compressed out of the main
file. Load it only when a route condition needs more detail.

Design rationale lives in `WORKFLOW-MAP.md` at the repo root (repo checkout
only, not installed with the skill).

## Conditional stage selections

These selections supplement the canonical route; they do not replace its gate
semantics or start a new execution loop. At most one selected Controller owns
implementation, verification repairs, retries, pause, and termination. A
different Controller may start only after an explicit persisted handoff in
existing controller-native records. Stage Skills and verification tools report
work or evidence to that owner; they do not take ownership implicitly.

- S0: `project-session-manager` (multi-ticket parallel worktrees);
  `recall` (resume prior work); `deepinit` (first entry into a new codebase).
- S1: `grill-with-docs` (need ADR + glossary as you go);
  `deep-interview` (extreme ambiguity, Socratic probing).
- S2: use the selected Spec Adapter; `spec` fits when that adapter's output is
  issues/tickets for a GitHub flow; `domain-modeling` adds ubiquitous language.
  Constitution handling is ensure/read-only: identify and read the applicable
  governance first. Use `speckit-constitution` only when Spec Kit is the
  selected adapter and missing or outdated governance must be created or
  amended within the delivery authorization; never run or rewrite it
  unconditionally for each task.
- S3: under a selected Spec Kit adapter, `speckit-plan` + `speckit-tasks` can
  provide the heavy doc pipeline;
  `plan-eng-review` / `plan-ceo-review` / `plan-design-review`
  (large/high-risk multi-view review); use `speckit-analyze` /
  `speckit-checklist` only with that adapter for spec-plan-tasks consistency;
  `arena` / `principle-exhaust-the-design-space` fit no-precedent designs that
  need 2–3 prototypes first.
- S4: `implement` can perform a small/medium build from an existing spec or
  tickets as a Stage Skill under the selected owner. `executing-plans` may be
  selected as the sole Controller in a no-subagent environment. `autopilot` or
  `ralph` may be selected as the sole Controller for an unattended long run;
  the route also selects the required S8 `show-me-your-work` capture. Do not
  introduce any of them as an ad-hoc replacement while another Controller owns
  the route.
- S5: `self-verifying-tests` is now a canonical adversarial branch (see SKILL.md),
  not an alternative; remaining selections include `create-verification-skill` +
  `maintain-verification-skill` (project-level verify);
  language rigs (`cpp-testing`, etc.). Verification failures return to S4;
  the selected Controller owns repairs and obtains fresh S5 evidence. Do not
  start a verifier-native fix loop inside S5 or S6.
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
