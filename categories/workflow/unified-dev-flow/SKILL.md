---
name: unified-dev-flow
version: "2026.09.12-1"
synced-at: "2026-09-12T18:37:53"
description: 当开始非简单的功能开发、修 bug、重构或迁移，需要决定走哪些阶段、调用哪些技能、走多深时使用。当用户问该用什么流程或技能时使用。触发词：统一流程 / 标准流程 / 开发流程 / 完整流程 / 走流程 / 端到端开发 / 该用什么技能 / 帮我选流程 / 怎么推进这个需求 / 规范流程。Use when deciding which dev workflow/skills to use for a non-trivial coding task.
---

# Unified Dev Flow

A **policy-driven thin router**. It owns route selection, gate semantics,
evidence freshness, resume rules, and delivery limits. It delegates domain work
and execution loops to existing skills/controllers and never re-implements them.

1. **Resume before classification.**
2. **Read before committing.**
3. **Intent selects the base route.**
4. **Complexity determines planning depth.**
5. **Risk determines assurance depth.**
6. **One controller owns execution at a time.**
7. **Any intersecting source change invalidates stale evidence.**
8. **No completion claim without fresh evidence.**
9. **Delivery never exceeds authorization.**

## R0 Read-only Recon

Before Entry Gate or policy resolution, inspect repository/worktree state,
project constraints, relevant code, test entry points, active workflow state,
and available spec backends without writing files. `.codegraph/` is
project-local and optional: use it first when it already exists and project
instructions require it; never initialize it here.

## Resume Gate

Check existing `.superpowers/sdd/` ledgers (including nested `progress.md`),
active specifications/changes, and controller-native state before creating a
new route. Compare goal, branch/worktree, recorded base/head versus current
HEAD, relevant task diff, and controller state:

- **FRESH**: no applicable recorded work; continue to Entry Gate.
- **MATCH**: resume the recorded controller and stage, without reclassification.
- **COMPATIBLE_DRIFT**: reconcile changed scope and evidence, then resume.
- **CONFLICTING_DRIFT**: invalidate the stale plan/state and return to Entry Gate.

Use existing native records; legacy resume does not require a unified runtime
or conversion of its ledger.

## Phase Two Runtime

After policy resolution, an eligible non-`patch` Route may be pinned as a
`RouteContract` through `scripts/unified-workflow init --goal "<goal>" --route-file route.json
--project-root <project> --work-id <id> --request-id <id> --json`.
The Router remains policy authority; the Kernel enforces the pinned finite
obligations described in [policy-model.md](references/policy-model.md).
Adapter execution and controller ownership stay external. The runtime does not
start agents, create worktrees, or initialize `.codegraph/`.

Use `--help` on each CLI command for its named JSON file inputs. Mutations
require a request ID and optionally an expected sequence. Verification selects
a registered `command_id` from the TaskContract; trusted local execution has
caller authority and provides no OS sandbox. `review record` passes the Gate's
wait-for-review check and records the external assertion in one atomic Store
batch under the caller's request ID.
`status --json` and `replay --json` expose the same canonical replayed state,
including the pinned goal/route, review rounds, blockers, timestamps, and log head;
runtime records live only under the target project's `.unified-dev-flow/`.
Authorized initialization first validates root Git metadata with read-only
`git rev-parse --absolute-git-dir`, then adds a local Git ignore rule (with a
minimal root `.gitignore` fallback when required) and validates it with `git check-ignore`.
Existing `.omc/` and `.superpowers/sdd/` records retain their native roles.

## Entry Gate (first commitment after recon)

For fresh or conflicting work, emit four task-specific sections before choosing
a new route or writing implementation files. Resumed work must reconcile its
existing gate with current evidence before further edits.

1. **理解和假设** → S1/S2: state the problem, uncertain assumptions, project
   constraint docs actually read, and authorized `delivery_target`.
2. **最小方案 + 文件范围** → S3: describe the minimum change and list files
   located through R0 evidence; prefix new files `NEW:`. No implementation yet.
3. **范围纪律** → S6: map files to requested behavior, root-cause dependencies,
   required tests, or migration/build artifacts; record unrelated findings and
   any measurement exemptions (e.g. no-baseline `health` waiver) so waivers stay auditable.
4. **验证计划** → S5: name the `proof_mode`, its baseline/reproduction or unmet
   acceptance evidence, and the exact commands that will prove the change.

Before gated edits, record the statement in `.omc/entry-gate-<sessionID>.md`
using four `##` headings containing the labels above, a file-scope list, and
≥150 characters total; see [enforcement.md](references/enforcement.md) for the
existing checker contract. Micro work uses the same substantive four sections.
Amend the gate before editing newly discovered root-cause dependencies.

## Policy Resolution

`Route = Resume + Intent + Complexity + Risk + Domain + Delivery`

Read [policy-model.md](references/policy-model.md) for the detailed dimension,
proof, scope, and adapter rules. Resolve the six axes once, then state the stage
subset, `spec_backend`, controller (one or none), `proof_mode`,
`assurance_level`, and `delivery_target` together as one route decision.

| Intent | Base route |
|---|---|
| Bug | S0 → debug → S4 → S5 → S6 → S7(target) |
| Feature | S0 → S1/S2/S3 (trim by complexity) → S4 → S5 → S6 → S7(target) |
| Refactor | S0 → S3 → S4 → S5 → S6 → S7(target) |
| Migration | S0 → S2/S3 → S4 → S5 → S6 → S7(target) |
| Research | S1 → S3 → S8; stop without delivery |
| Config | S0 → S4 → S5 → S6 as required by risk → S7(target) |

Before S4, insert complexity-required planning from the policy model; compose
the base route with risk/domain overlays and the policy's capture selection.
Complexity changes planning only. **Bug + Micro + Security +
Production** means light planning plus adversarial assurance plus production
review, stopping at the authorized delivery target.

Example: **Feature + Large + Security + API + Working Tree** composes
S0 → S1 → S2(selected adapter) → S3(plan review/checkpoints) → S4(one
eligible controller + API specialist) → S5(adversarial) → S6 → S7(working tree).
It stops with verified, reviewed code and local planning/checkpoint artifacts.

## Controller Ownership Invariant

At most one Controller owns the execution loop, retries, pause, and termination;
controller-free routes are allowed. Controllers include `speckit-chain`, an
OpenSpec change flow, `executing-plans`, `subagent-driven-development` (full
SDD execution), `autopilot`, `ralph`, `team`, and `figure-it-out`. Never nest
their main loops. A change of owner requires an
explicit persisted handoff in existing controller-native records before the
next owner starts. Full SDD execution must be selected as the controller or
receive that handoff; its individual delegated agents are workers.

Stage Skills perform stages; Workers perform delegated units; Reviewers judge
without editing reviewed source; Principles constrain all roles; Domain
Specialists add method/evidence. Dispatch helpers such as
`dispatching-parallel-agents`, and the local pstack `swarm`, are workers under
the chosen owner. Local `swarm` is distinct from OMC's retired alias.
The router's gate and escalation requirements govern all delegation, including
SDD: escalate after three NEEDS_FIXES rounds even if a delegated skill allows
more retries.
Before selection or resume, apply the policy model's Controller Eligibility
checks: delivery ceiling, three-round escalation, evidence invalidation and
selected adapter. Full SDD requires authorized local commits; an unadapted
`speckit-chain` is ineligible. Missing capabilities require another eligible
owner, a controller-free route, or an explicit persisted handoff.

## Spec Adapter Resolution

Select one backend in order: safely resumable active backend → available
explicit user choice → project configuration → sole initialized backend →
`unified` light path. If both `openspec/` and `.specify/` exist with no resolved
ownership, stop and request ownership before proceeding. Spec Kit and OpenSpec
must never maintain the same request concurrently. External `speckit-*`
commands require initialized Spec Kit; use only adapters/controllers available
in the target environment. Adapter selection does not authorize nested loops.
Apply the policy's artifact contract: Unified uses a named local path;
`to-spec` requires authorized/configured issue publication. Spec Kit uses the
trimmable sequence with constitution read-only by default; OpenSpec resolves
the installed profile. Detailed procedures live only in the policy model.

## Proof Before Change

Keep RED-first for bugs (failing test or stable reproduction) and features
(unmet acceptance test); TDD remains their default method. For other intents
and domain overlays, select the proof mode from the policy reference before
editing: characterization, dry-run/rollback, benchmark, security assertion,
config validation, or visual/E2E evidence as applicable.

Apply the policy's risk-to-assurance mapping independently of complexity.
Reviewer counter-cases are adversarial checks, not mutation testing.

## Selected Stage Skills

Load only the selected stages and needed specialists; each keeps its own
procedures. Alternatives live in [alternatives.md](references/alternatives.md)
(load on demand); the repo's `WORKFLOW-MAP.md` is not installed with this skill.

| Stage | Delegate to | Exit when |
|---|---|---|
| S0 Prepare | `using-git-worktrees` as needed; `health` baseline before S4 where a comparison baseline can exist (single-edit typo-class changes exempt with §3 waiver) | Workspace ready; resume resolved; applicable baseline captured |
| S1 Intent | `brainstorming`; PRD: `parse-prd`; terms: `domain-modeling` | Scope confirmed; blocking assumptions resolved |
| S2 Spec | Selected Spec Adapter and its eligible local/publishing path | Spec and governing principles named; ambiguity resolved |
| S3 Plan | `writing-plans`; architecture: `architect`; large: `plan-eng-review`; design: `prototype` | Plan at required depth with verification, rejected alternatives, and principles check |
| S4 Implement | Chosen controller and its delegated workers; bugs/features: `test-driven-development`; DB: `create-migration` | Planned change and intent-appropriate tests implemented |
| S5 Verify | `verification-before-completion`, `principle-prove-it-works`; E2E: `e2e-testing`; cross-layer: `self-verifying-tests` | Fresh command evidence meets selected proof and assurance requirements |
| S6 Review | `health` + `google-code-review`; spec-bearing: `code-review`; per policy Review Selection (no-baseline edits exempt from `health`, waiver in §3); every S6 declares via `.omc/review-<session>.md` | MERGE_READY or explicit waiver within authorization |
| S7 Deliver | `finishing-a-development-branch` / `ship` within target; unattended: `ai-release-engineer`; deployment: `deployment-patterns`, `canary` | Fulfill delivery target |
| S8 Capture | `knowledge-capture`; `show-me-your-work` where selected by policy Capture Selection | Findings and required decision trail filed |

## Evidence and Review Gates

- No S4 without the required planning depth and first proof; micro/small
  compress planning, never verification. Large plan review must pass first.
- Every route reaching S6 requires `health` and `google-code-review`, except
  no-baseline edits (single-edit typo-class changes with nothing structural to
  compare) which require `google-code-review` with the `health` waiver recorded
  in Entry Gate §3.
  Spec-bearing routes add `code-review`. Select `interrogate` for adversarial
  assurance/risk or the independent-review fallback, never complexity alone.
  Select `ai-slop-cleaner --review` only for actual cleanup/slop/refactor evidence;
  keep reviewer-only posture. Compare `health` with baseline;
  regression blocks; unavailable → `codehealth-mcp` or explicit waiver.
- Independent reviewer receives spec/acceptance criteria, current diff, tests,
  and fresh evidence, not merely implementer claims. Use a different model/lab
  when available; otherwise require `interrogate` on routes with a baseline,
  while no-baseline edits may use same-model review with the provenance labeled
  explicitly (e.g. `reviewer: claude (self, no-baseline)`). Reviewer judges; S4 edits.
- S6 arrival is declared on disk, not in prose: `.omc/verify-<session>.md`
  (S5 evidence) and `.omc/review-<session>.md` (verdict + reviewer + round).
  No artifact = S6 not reached = completion claim invalid. The Stop hook
  `--check-review` enforces this; see [enforcement.md](references/enforcement.md).
- Any source or test change invalidates intersecting verification evidence
  and review verdicts, including changes made during cleanup or review.
  Reverify and re-review affected work before claiming completion.
- NEEDS_FIXES follows **S6 → S4 → S5 → S6**. After three NEEDS_FIXES review
  rounds, escalate to a human; do not bypass escalation by changing agents.
- Live/production changes require `production-risk-review` before S7.
  Unattended `autopilot`/`ralph` delivery also requires `ai-release-engineer`.

## Delivery Limits

Apply the policy model's Delivery Targets at every stage and to every delegate.
Default implementation requests to `working_tree`; higher targets require
explicit authorization. S7 stops at the authorized ceiling. For `patch`, keep
recon/proof read-only and return the Entry Gate and proposed changes in the
response without artifacts.

## Cross-cutting and Bypass

- Domain overlays: UI → `frontend-design` / `ui-ux-pro-max`; API → `api-design`;
  database → `access-pattern-driven-data-modeling` / `database-migrations`;
  performance → `performance-tuning`; docs → `technical-writing` /
  `html-first-workflow`; infrastructure → `deployment-patterns`.
- Debug: `systematic-debugging` → `root-cause-hunter` → `paranoid-debugging`;
  deep intent: `deep-interview` / `deep-dive`; refactor:
  `clean-code-behavior-preserving-refactoring` / `entropy-reduction`.
- Context/principles: `context-save` / `context-restore`, `strategic-compact`,
  `principle-fix-root-causes`, `principle-sequence-verifiable-units`, and
  `principle-guard-the-context-window`; load other principles on demand.
- Pure non-code domain actions go directly to their specialist. Honor an
  explicitly chosen workflow; safely resumable active work retains its owner.
  Trivial edits can skip staged routing but still meet applicable write gates.
