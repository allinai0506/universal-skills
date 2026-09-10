# Unified Dev Flow Policy Model

This reference defines routing policy only. The router selects existing stage
skills and adapters; it does not reproduce their implementation procedures or
create a phase-two runtime, ledger, or execution backend.

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
Resolution combines independent dimensions, chooses exactly one controller (or
none), and then selects the needed S0–S8 subset.

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

## Policy Dimensions

Policy is a composition of these exact values:

```yaml
resume: fresh | match | compatible_drift | conflicting_drift
intent: bug | feature | refactor | migration | research | config
complexity: micro | small | medium | large | intractable
risk: [auth, permission, security, money, data_integrity, production, concurrency, migration]
domain: [ui, api, database, performance, docs, infrastructure]
delivery_target: patch | working_tree | commit | pr | merge | deploy
spec_backend: unified | speckit | openspec
controller: exactly one controller or none
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
| micro | The Entry Gate file list is the compressed plan. |
| small | Use brief implementation steps; no separate heavy specification. |
| medium | Require written spec, plan, and tasks through one Spec Adapter. |
| large | Require complete specification, plan review, task slices, and checkpoints. |
| intractable | Require a playbook, audit trail, and human escalation points. |

Complexity never reduces the assurance level required by risk.

## Risk and Assurance Depth

- **deterministic**: execute relevant build, test, lint, schema, dry-run, or
  equivalent real checks.
- **adversarial**: add counterexamples such as authorization violations,
  boundaries, cross-layer inconsistencies, attack/reproduction cases, or state
  transitions.
- **mutation**: run real mutation testing only for suitable core logic when a
  real runner is available.

Auth, permission, security, money, data integrity, critical state machines,
and concurrency require at least adversarial proof. Do not manufacture mutation
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

## Controller Roles

- **Controller** owns the main loop, retries, pause, and termination.
- **Stage Skill** completes a selected stage but does not own the global loop.
- **Worker** performs a delegated unit of work.
- **Reviewer** independently judges evidence and does not modify reviewed
  source.
- **Principle** constrains all roles.
- **Domain Specialist** supplies domain-specific method and evidence.

Exactly one Controller owns execution at a time. A handoff to another
controller requires an explicit recorded handoff. Candidate controllers include
`speckit-chain`, an OpenSpec change flow, `executing-plans`, `autopilot`,
`ralph`, `team`, and `figure-it-out`.

OMC's retired `swarm` alias is distinct from the local pstack `swarm` worker
skill. This policy does not delete the local skill or treat the retired alias as
the local fan-out worker tool.

## Spec Adapter Resolution

Choose exactly one spec backend in this order:

1. Resume the backend of a safely resumable active change or specification.
2. Honor an explicit user choice when that backend is available in the target project.
3. Use a backend declared by project configuration.
4. Use the sole initialized backend detected in the project.
5. Fail closed and request ownership when both `openspec/` and `.specify/`
   coexist without explicit ownership.
6. Otherwise select the Unified Dev Flow light path (`unified`).

Spec Kit and OpenSpec never maintain the same request concurrently. This policy
names adapters only; it does not prescribe their internal commands.

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
