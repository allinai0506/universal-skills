# Unified Dev Flow Policy Model

This reference is the authoritative source for detailed routing policy. The router selects existing stage
skills and adapters; it does not reproduce their implementation procedures.
The optional phase-two Kernel enforces a pinned contract from this policy;
the Router retains policy selection and Adapter execution remains external.

## Resolution Order

`R0 Read-only Recon → Resume Gate → Entry Gate → Policy Resolution → Controller → selected S0–S8 stages.`

R0 establishes the facts before the router commits scope, proof, or commands:
project instructions, repository and worktree state, active ledgers or changes,
project manifests and test entry points, spec backends, and the relevant code
and call paths. R0 permits reads only.

`.codegraph/` is a project-local optional index. When the target project already
contains it, follow that project's `AGENTS.md` and use CodeGraph during R0;
otherwise continue with normal read-only discovery. The router never initializes it.

The Resume Gate runs before classification. The Entry Gate records R0-backed
understanding, minimum file scope, scope discipline, and a proof plan. Policy
Resolution combines independent dimensions, chooses at most one controller
(controller-free routes are allowed), and then selects the needed S0–S8 subset.

## Resume Semantics

Compare the recorded goal fingerprint, branch and worktree, recorded base/head,
current HEAD, relevant task diff, and the native state of the recorded
controller.

- **FRESH**: no applicable recorded work exists; continue to Entry Gate.
- **MATCH**: goal fingerprint, branch/worktree, head ancestry, relevant diff,
  and controller state agree; resume the recorded controller and stage.
- **COMPATIBLE_DRIFT**: the goal and ownership still agree, while recorded and
  current heads or relevant diff differ in a reconcilable way; reconcile the
  changed evidence and scope before resuming.
- **CONFLICTING_DRIFT**: a different goal, incompatible branch/worktree,
  divergent relevant diff, or unusable controller state makes prior work
  unsafe to resume; invalidate conflicting state and return through Entry Gate.

Phase one can read existing `.superpowers/sdd/progress.md`, `.specify/`,
`openspec/changes/`, and controller-native state. It does not create a unified
ledger.

## Runtime RouteContract Handoff

After resolving a Route, the Router may emit schema-version-1 `RouteContract`
for authorized `working_tree` or higher delivery. `patch` cannot initialize a
runtime. Pin `resume`, `intent`, `complexity`, `risks`, `domains`,
`delivery_target`, `spec_backend`, `controller`, `proof_mode`, `assurance_level`,
`review_limit`, and `source.policy_version` / `source.policy_sha256` along with
these finite obligations:

| Obligation | Router emission and Kernel check |
|---|---|
| `verification_claims` | Required claim set drawn from `deterministic`, `adversarial`, `mutation`, according to the resolved assurance. Fresh successful registered commands must collectively cover it; selected required commands must also pass. |
| `accepted_review_provenance` | Explicit allowed subset of `cross_model`, `human`, `mock`; select suitable provenance for the resolved review policy. A fresh `MERGE_READY` assertion must bind current task, inputs, command contracts, and evidence. |
| `required_delivery` | Required endpoint at or below the authorized `delivery_target`; delivery must bind the current acceptance set and workspace with provenance. |

The `review_limit` retains the Router's three-round escalation ceiling; a
smaller selected limit is respected. Claims and review provenance are declared
contracts, not automatic certification that an external reviewer is independent
or that arbitrary tests establish a claim. Planning, specialist selection,
production review, and external delivery actions remain Router/Adapter duties.
The Kernel records supplied delivery evidence; it does not commit, publish,
merge, or deploy. Legacy resume continues from native records and does not
require a Kernel run or migration.

The CLI reads UTF-8 JSON from `--route-file`, `--task-file`,
`--assertion-file`, and `--provenance-file`. `--report-file` contains
`{report: {summary: ...}, workspace_revision: ...}`; `--delivery-file` contains
`{delivery_target, acceptance_set_sha256, workspace_revision, provenance}`.
These are JSON object shapes; use quoted JSON keys in files. Verification
accepts only `--command-id`, never an arbitrary command string. External
callers can use the Provider API for workspace observations; recorded successful
verification evidence in `status --json` supplies review bindings.

`review record` composes `WAIT_FOR_REVIEW` and `RECORD_REVIEW` through Store in
one atomic batch. The caller request ID and complete assertion fingerprint
cover success or denial of either Gate; there is no partial durable wait step.
An explicit expected sequence is authoritative. When omitted, Store binds to
the current head under its writer lock, or the original reservation for a retry.
Existing tasks already waiting for review continue directly to `RECORD_REVIEW`.
Other mutations map to their corresponding Gate command.
`request status --request-id <id>` inspects a reservation;
`request resolve --request-id <id> --resolution-file resolution.json` resolves
that existing in-doubt attempt using `{outcome, actor: {type, id}, note}`.
Outcomes are `abandoned` or the manually verified `success`, `denied`, or
`provider_failure`; resolution never reruns execution or supplies acceptance.
Its expected-sequence check occurs under the Store writer lock.

All mutations require `--request-id`; optional `--actor-file` supplies
`{type, id}` for ordinary commands (default `{type: cli, id: local}`). Request
resolution uses its mandatory document actor instead. `--json` emits one
canonical object. Exit codes are `0` success, `2` invalid arguments/contract,
`3` Gate denial, `4` corrupt state, `5` lock busy, `6` Provider/verification
failure, and `7` request in doubt. Status/replay reconstruct state from events,
without maintaining a snapshot or writing legacy control directories.

## Policy Dimensions

Policy is a composition of these exact values:

```yaml
resume: fresh | match | compatible_drift | conflicting_drift
intent: bug | feature | refactor | migration | research | config
complexity: micro | small | medium | large | intractable
risk: [auth, permission, security, money, data_integrity, production, state_machine, concurrency, migration]
domain: [ui, api, database, performance, docs, infrastructure]
delivery_target: patch | working_tree | commit | pr | merge | deploy
spec_backend: unified | speckit | openspec
controller: at most one controller; none is allowed
proof_mode: derived from intent and domain
assurance_level: deterministic | adversarial | mutation
```

`intent` selects a base lifecycle; `complexity` changes planning depth only;
`risk` selects assurance independently; `domain` adds specialists without
changing controller ownership. `delivery_target` is an authorization ceiling,
not a prediction of what will happen.

## Intent Base Routes

| Intent | Base stages |
|---|---|
| bug | S0 → debug → S4 → S5 → S6 → S7(target) |
| feature | S0 → S1/S2/S3 (trimmed by complexity) → S4 → S5 → S6 → S7(target) |
| refactor | S0 → S3 → S4 → S5 → S6 → S7(target) |
| migration | S0 → S2/S3 → S4 → S5 → S6 → S7(target) |
| research | S1 → S3 → S8; stop without delivery |
| config | S0 → S4 → S5 → S6 as required by risk → S7(target) |

Domain and risk signals are overlays, not mutually exclusive intents.

## Complexity and Planning Depth

| Complexity | Planning depth |
|---|---|
| micro | The Entry Gate file list is the compressed plan. No-baseline edits stay review-only per Review Selection. |
| small | Use brief implementation steps; no separate heavy specification. `health` baseline only on risk. |
| medium | Require written spec, plan, and tasks through one Spec Adapter. |
| large | Require complete specification, plan review, task slices, and checkpoints. |
| intractable | Require a playbook, audit trail, and human escalation points. |

Before S4, insert the planning required by the selected complexity into the
base route. Complexity changes planning depth only; it never selects assurance
or adversarial reviewers. Risk independently determines assurance.

## Capture Selection

| Route condition | S8 requirement |
|---|---|
| research | Select S8 to capture findings; stop without delivery. |
| intractable | Select S8 for the required audit trail and decision capture. |
| large | Full spec, plan review, slices, and checkpoints; no automatic S8. |
| unattended | May select S8 with `show-me-your-work` when decision capture is applicable. |

Capture respects the delivery ceiling: `patch` keeps findings and the decision
trail in the response; other targets may use authorized local artifacts.

## Risk and Assurance Depth

- **deterministic**: execute relevant build, test, lint, schema, dry-run, or
  equivalent real checks.
- **adversarial**: add counterexamples such as authorization violations,
  boundaries, cross-layer inconsistencies, attack/reproduction cases, or state
  transitions.
- **mutation**: run real mutation testing only for suitable core logic when a
  real runner is available.

| Risk signal | Required assurance or gate |
|---|---|
| auth | At least adversarial proof. |
| permission | At least adversarial proof. |
| security | At least adversarial proof. |
| money | At least adversarial proof. |
| data_integrity | At least adversarial proof. |
| state_machine | Critical state machines require at least adversarial proof. |
| concurrency | At least adversarial proof. |
| migration | Dry-run, forward and rollback validation; data_integrity also requires adversarial proof. |
| production | `production-risk-review` before S7, retaining assurance required by other risks. |

Do not manufacture mutation
requirements for CSS, layout, generated code, configuration, or migration glue;
use applicable deterministic or adversarial evidence instead.

## Domain Adapters

| Domain signal | Existing specialist skills |
|---|---|
| UI | `frontend-design`, `ui-ux-pro-max` |
| API | `api-design` |
| database | `access-pattern-driven-data-modeling`, `create-migration` when needed |
| performance | `performance-tuning` |
| docs | `technical-writing`, `html-first-workflow` |
| infrastructure | `deployment-patterns`, with `database-migrations` for migrations |

These specialists contribute domain method and evidence; they do not become the
controller merely by being selected.

## Delivery Targets

Delivery targets are increasing authorization ceilings:

| Target | Authorized endpoint |
|---|---|
| patch | Return a proposed patch only; do not write the worktree. |
| working_tree | Modify and verify locally; stop in the worktree. |
| commit | Create a local commit. |
| pr | Push and create a pull request. |
| merge | Merge, but do not deploy. |
| deploy | Deploy only after applicable production gates. |

Default to `working_tree` when the user asks to fix or implement without a
specific delivery authorization. Any higher target requires explicit user
authorization. S7 means “fulfill delivery target,” not an automatic deployment.
The ceiling applies at every stage and to every delegate, including hooks and
capture. For `patch`, recon/proof remain read-only; return the Entry Gate,
specification, and proposed patch in the response without writing artifacts.
Issue-tracker publication requires separate explicit authorization and configured
tracker access; a local delivery target does not authorize publication.

## Controller Roles

- **Controller** owns the main loop, retries, pause, and termination.
- **Stage Skill** completes a selected stage but does not own the global loop.
- **Worker** performs a delegated unit of work.
- **Reviewer** independently judges evidence and does not modify reviewed
  source.
- **Principle** constrains all roles.
- **Domain Specialist** supplies domain-specific method and evidence.

At most one Controller owns execution at a time; controller-free routes are
allowed. A handoff to another controller requires an explicit recorded
handoff. Candidate controllers include `speckit-chain`, an OpenSpec change
flow, `executing-plans`, `subagent-driven-development` (full SDD execution),
`autopilot`, `ralph`, `team`, and `figure-it-out`.

OMC's retired `swarm` alias is distinct from the local pstack `swarm` worker
skill. This policy does not delete the local skill or treat the retired alias as
the local fan-out worker tool.

## Controller Eligibility

Before selecting or resuming a Controller, inspect its installed native
contract and any adapter/handoff against all of these capabilities:

| Capability | Required behavior |
|---|---|
| delivery_target | Honor the ceiling at every stage, including native commits and hooks; never push, merge, or deploy above it. |
| escalation | Escalate after three NEEDS_FIXES rounds, even if the native loop allows more; changing agents does not reset the count. |
| evidence | Invalidate intersecting verification evidence and review verdicts after source or test changes; reverify and re-review. |
| spec_backend | Honor the selected adapter, its artifacts, constitution restrictions, slices and convergence. |

Full `subagent-driven-development` requires local commits for implementation
and review packages. It is not eligible below `commit` unless the user explicitly
selects full SDD and authorizes its required local commits. Record that narrow
commit exception in the route; it grants no push, merge, or deploy authority.
Selecting full SDD alone does not authorize the commits.

`speckit-chain` is only a candidate when a verified compatible adapter/handoff
can honor this contract. Its current unconditional constitution rewrite and
one-shot implementation behavior are incompatible with the selected adapter's
read-only constitution and sliced execution requirements. Do not select the
unadapted chain or assume a prose instruction disables its native behavior.

If capabilities are missing or unverified, reject that Controller; choose a
compatible controller-free route or another eligible owner. Safely resumed
work retains ownership only after these checks; otherwise pause for an explicit
persisted handoff in existing controller-native records. Never nest main loops.

## Spec Adapter Resolution

Choose exactly one spec backend in this order:

1. Resume the backend of a safely resumable active change or specification.
2. Honor an explicit user choice when that backend is available in the target project.
3. Use a backend declared by project configuration.
4. Use the sole initialized backend detected in the project.
5. Fail closed and request ownership when both `openspec/` and `.specify/`
   coexist without explicit ownership.
6. Otherwise select the Unified Dev Flow light path (`unified`).

Spec Kit and OpenSpec never maintain the same request concurrently. If a chosen
backend or required capability is unavailable, stop and report the mismatch;
do not silently switch a user's explicit choice or initialize tools. A resolved
backend still must meet the following artifact contract within authorization.

### Unified Light Adapter

Use a local specification artifact compatible with `working_tree`: follow the
project's existing docs convention, or use `docs/specs/<task>.md` when none
exists. Name the path in the route. Medium requires spec/plan/tasks, which may
be sections in that artifact or linked local files; large requires the complete
specification and reviewed slices/checkpoints. For `patch`, return the proposed
artifact content and path in the response without writing it.

`to-spec` publishes to the project issue tracker as part of its native procedure.
It is eligible only when issue-tracker publication is explicitly authorized and
tracker access plus triage labels are configured. Otherwise use the local
artifact path; do not treat `to-spec` as a local-only writer.

### Spec Kit Adapter

Require initialized `.specify/` and available installed commands. Expose this
trimmable sequence, retaining the artifacts and gates required by the route:

`ensure/read-only constitution → specify → clarify → plan → checklist → tasks → analyze → implement slices → converge`

Read existing constitution by default. Create or update constitution only when
missing or when the user explicitly changes project principles, within delivery
authorization. Perceived age or a routine task is not permission to rewrite it.
Trim optional stages according to scope and unresolved ambiguity, recording the
reason; preserve selected proof, review and planning requirements. Large work
uses slices and checkpoints under the same eligible Controller. Convergence
checks the implementation against spec/plan/tasks; repairs return through S4,
fresh S5 and S6 within the router's three-round escalation limit. Inspect native
commands and hooks before dispatch; unavailable required stages need a verified
compatible handoff or a reported blocker, not an invented command.

### OpenSpec Adapter

Resolve the installed `core` or `expanded` profile from target-project commands
and configuration; do not hard-code command counts. Read the installed profile's
artifact dependencies and available change flow, then select the stages needed
for the route's specification, planning, verification and capture requirements.
An unknown or unavailable profile is a blocker until resolved; do not install,
change profiles, or invent missing commands implicitly.

## Proof Before Change

| Work | First proof mode |
|---|---|
| Bug | Failing test or stable reproduction script. |
| Feature | Acceptance test not yet satisfied. |
| Refactor | Passing characterization or regression baseline before change. |
| Migration | Dry-run plus forward and rollback validation. |
| Performance | Reproducible benchmark baseline. |
| Security | Exploit/reproduction or security assertion. |
| Config | Schema, lint, or configuration-load validation. |
| UI | Visual or E2E acceptance evidence. |

TDD remains the default implementation method for bugs and features, but no
single proof form is forced onto every intent.

## Review Selection

| Condition | S6 selection |
|---|---|
| ordinary | `health` against the S4 baseline and `google-code-review`. |
| spec-bearing | Add `code-review` for spec consistency. |
| adversarial assurance/risk | Add `interrogate` and applicable risk specialists. |
| independent reviewer unavailable | If a different-model/lab reviewer is unavailable, require `interrogate` as the fallback on routes with a baseline; no-baseline routes may use labeled same-model review instead. |
| cleanup evidence | Select `ai-slop-cleaner --review` only with actual cleanup/slop/refactor evidence such as duplication, dead code or needless wrappers; use reviewer-only posture after a cleanup draft. |

Measurement applicability: `health` compares against an S4 baseline. A route
that cannot produce one — a single-edit typo-class change with nothing
structural to compare — is exempt from `health` (baseline and compare), never
from `google-code-review`. Record the exemption in Entry Gate §3 (范围纪律).
This is not complexity selecting reviewers: the reviewer set is identical for
every route; only an inapplicable measurement is skipped, and the skip stays
auditable via the waiver.
Complexity alone never selects `interrogate`. Generic refactoring without
simplification/slop evidence does not select `ai-slop-cleaner`. Any S6 reviewer
reports repairs to S4 without editing reviewed source. Health regression blocks;
if unavailable, use `codehealth-mcp` or an explicit waiver. Live/production
changes require `production-risk-review` before S7; unattended delivery also
requires `ai-release-engineer`.

## Scope Mapping

Every changed file must map to at least one of: requested behavior, a root-cause
dependency, a required test, or a required migration/build artifact. Record
unrelated findings without changing them. If a root-cause dependency expands
the scope, amend the Entry Gate before editing the additional file.

## Evidence Invalidation and Review Loop

Any source or test change invalidates intersecting verification evidence and
review verdicts. Completion claims require fresh evidence.

`NEEDS_FIXES` always follows `S6 → S4 → S5 → S6`: implementation/fix, fresh
verification, then independent review. A reviewer judges spec, diff, tests, and
evidence, while the S4 role makes repairs. After three `NEEDS_FIXES` review
rounds, escalate to a human rather than continuing the loop.
