# Unified Dev Flow Policy Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `unified-dev-flow` into a policy-driven thin router whose route is composed from resume state, intent, complexity, risk, domain, and delivery target.

**Architecture:** Keep `SKILL.md` as the compact executable router and move detailed decision tables into a new `references/policy-model.md`. A stdlib-only static contract test locks the router invariants across `SKILL.md`, the policy reference, the enforcement reference, and `WORKFLOW-MAP.md`; existing Entry Gate mechanics remain compatible during phase one.

**Tech Stack:** Markdown skill contracts, Python 3 standard library, existing `quick_validate.py`, repository `sync.sh`.

## Global Constraints

- Phase one only: do not implement Gate Kernel, `.unified-dev-flow/runs/`, event logs, Task Contracts, Providers, or Herdr integration.
- `.codegraph/` is project-local and optional: use it during R0 only when the target project already contains it; never initialize it from this router.
- Preserve the four existing Entry Gate headings and `.omc/entry-gate-<sessionID>.md` compatibility.
- Preserve unrelated working-tree changes; execute from an isolated worktree because the current checkout already contains unrelated modifications.
- One controller may own execution at a time; controllers may call workers, reviewers, principles, and stage skills, but not nest another controller without an explicit handoff.
- Complexity controls planning depth; risk controls assurance depth.
- Default delivery target for an unqualified “implement/fix” request is `working_tree`; never escalate delivery authority implicitly.
- Do not modify `categories/workflow/speckit-chain/SKILL.md` in phase one; the Router must stop depending on its current one-shot behavior.

## File Map

- `categories/workflow/unified-dev-flow/scripts/test_router_policy.py`: deterministic static acceptance test for the phase-one policy contract.
- `categories/workflow/unified-dev-flow/references/policy-model.md`: detailed six-axis policy, proof modes, controller roles, Spec Adapter resolution, and state-transition semantics.
- `categories/workflow/unified-dev-flow/SKILL.md`: compact executable router that performs R0, resume, Entry Gate, policy resolution, and delegates stage work.
- `categories/workflow/unified-dev-flow/references/enforcement.md`: mechanical Entry Gate documentation updated to state that the artifact is produced after R0 and records Proof Mode rather than universal RED.
- `WORKFLOW-MAP.md`: repository design source aligned with the new policy model and stripped of contradictory legacy routes.
- `SKILLS-INDEX.md`, `GEMINI.md`, and synced metadata: generated only through `./sync.sh`; inspect generated diffs before committing them.

---

### Task 1: Lock the Phase-One Router Contract with a Failing Static Test

**Files:**
- Create: `categories/workflow/unified-dev-flow/scripts/test_router_policy.py`

**Interfaces:**
- Consumes: UTF-8 Markdown at the four phase-one contract paths.
- Produces: executable `main() -> int` behavior; exit `0` only when every required invariant is present and every retired invariant is absent.

- [ ] **Step 1: Create the static contract test**

Create the file with this complete implementation:

```python
#!/usr/bin/env python3
"""Static acceptance checks for unified-dev-flow phase-one policy routing."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "categories/workflow/unified-dev-flow/SKILL.md"
POLICY = ROOT / "categories/workflow/unified-dev-flow/references/policy-model.md"
ENFORCEMENT = ROOT / "categories/workflow/unified-dev-flow/references/enforcement.md"
MAP = ROOT / "WORKFLOW-MAP.md"

FAILURES: list[str] = []


def read(path: Path) -> str:
    if not path.is_file():
        FAILURES.append(f"missing-file:{path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def require(name: str, text: str, needle: str) -> None:
    if needle not in text:
        FAILURES.append(f"missing:{name}:{needle}")


def forbid(name: str, text: str, needle: str) -> None:
    if needle in text:
        FAILURES.append(f"retired:{name}:{needle}")


def main() -> int:
    skill = read(SKILL)
    policy = read(POLICY)
    enforcement = read(ENFORCEMENT)
    workflow_map = read(MAP)

    for needle in (
        "R0 Read-only Recon",
        "Resume before classification",
        "Intent selects the base route",
        "Complexity determines planning depth",
        "Risk determines assurance depth",
        "Controller Ownership Invariant",
        "Proof Before Change",
        "delivery_target",
        "S6 → S4 → S5 → S6",
        "Spec Adapter Resolution",
    ):
        require("skill", skill, needle)

    for needle in (
        "resume",
        "intent",
        "complexity",
        "risk",
        "domain",
        "delivery_target",
        "MATCH",
        "COMPATIBLE_DRIFT",
        "CONFLICTING_DRIFT",
        "deterministic",
        "adversarial",
        "mutation",
        "openspec/",
        ".specify/",
    ):
        require("policy", policy, needle)

    require("policy", policy, ".codegraph/")
    require("policy", policy, "project-local optional index")
    require("enforcement", enforcement, "R0 Read-only Recon")
    require("enforcement", enforcement, "proof_mode")
    require("map", workflow_map, "Resume + Intent + Complexity + Risk + Domain + Delivery")
    require("map", workflow_map, "Fulfill delivery target")

    for needle in (
        "Scale decides depth",
        "## Step 1 — Classify the task",
        "Large-feature one-shot",
        "Merged, deployed",
        "every diff-level mutant killed",
    ):
        forbid("skill", skill, needle)

    if skill.count("Controller Ownership Invariant") != 1:
        FAILURES.append("count:skill:Controller Ownership Invariant")

    if FAILURES:
        print("\n".join(f"FAIL {item}" for item in FAILURES))
        return 1
    print("All router policy checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
python3 categories/workflow/unified-dev-flow/scripts/test_router_policy.py
```

Expected: exit `1`, including `missing-file:categories/workflow/unified-dev-flow/references/policy-model.md` and retired legacy markers such as `Scale decides depth`.

- [ ] **Step 3: Commit the failing contract test**

```bash
git add categories/workflow/unified-dev-flow/scripts/test_router_policy.py
git commit -m "test: define unified flow policy router contract"
```

---

### Task 2: Add the Detailed Policy Model Reference

**Files:**
- Create: `categories/workflow/unified-dev-flow/references/policy-model.md`
- Test: `categories/workflow/unified-dev-flow/scripts/test_router_policy.py`

**Interfaces:**
- Consumes: approved design at `docs/superpowers/specs/2026-09-10-unified-dev-flow-policy-router-design.md`.
- Produces: stable vocabulary and resolution rules that `SKILL.md` can reference without duplicating tables.

- [ ] **Step 1: Write the policy reference with fixed sections**

Create a concise reference containing these headings in this order:

```markdown
# Unified Dev Flow Policy Model

## Resolution Order
R0 Read-only Recon → Resume Gate → Entry Gate → Policy Resolution → Controller → selected S0–S8 stages.

## Resume Semantics
Define FRESH, MATCH, COMPATIBLE_DRIFT, and CONFLICTING_DRIFT using goal fingerprint, branch/worktree, recorded head, current head, and relevant diff.

## Policy Dimensions
Define resume, intent, complexity, risk, domain, delivery_target, spec_backend, controller, proof_mode, and assurance_level using the exact values from the approved design.

## Intent Base Routes
Map bug, feature, refactor, migration, research, and config to their base stage subsets.

## Complexity and Planning Depth
Map micro, small, medium, large, and intractable without changing assurance depth.

## Risk and Assurance Depth
Define deterministic, adversarial, and mutation levels; require adversarial proof for auth, permission, security, money, data integrity, critical state machines, and concurrency.

## Domain Adapters
Map UI, API, database, performance, docs, and infrastructure signals to existing specialist skills.

## Delivery Targets
Define patch, working_tree, commit, pr, merge, and deploy as increasing authorization ceilings; default to working_tree.

## Controller Roles
Separate Controller, Stage Skill, Worker, Reviewer, Principle, and Domain Specialist. Record that OMC's retired swarm alias is distinct from the local pstack swarm worker skill.

## Spec Adapter Resolution
Resume the existing backend first; then explicit user choice; then project config; then a sole detected backend; fail closed when openspec/ and .specify/ coexist without ownership; otherwise use the Unified light path.

## Proof Before Change
Map Bug, Feature, Refactor, Migration, Performance, Security, Config, and UI to the approved first-proof modes.

## Scope Mapping
Every changed file maps to requested behavior, root-cause dependency, required test, or required migration/build artifact; amend Entry Gate before expanding scope.

## Evidence Invalidation and Review Loop
Any intersecting source or test change invalidates stale evidence and verdicts. NEEDS_FIXES always follows S6 → S4 → S5 → S6, with three review rounds before human escalation.
```

Write the actual rules under every heading; do not copy stage-skill implementation instructions into this reference.

Include this exact CodeGraph statement under Resolution Order:

```markdown
`.codegraph/` is a project-local optional index. When the target project already
contains it, follow that project's `AGENTS.md` and use CodeGraph during R0;
otherwise continue with normal read-only discovery. The router never initializes it.
```

- [ ] **Step 2: Run the policy test and inspect the remaining failures**

Run:

```bash
python3 categories/workflow/unified-dev-flow/scripts/test_router_policy.py
```

Expected: the missing policy-file failure is gone; failures remain for the legacy `SKILL.md`, enforcement reference, and workflow map.

- [ ] **Step 3: Commit the policy reference**

```bash
git add categories/workflow/unified-dev-flow/references/policy-model.md
git commit -m "docs: define unified flow policy model"
```

---

### Task 3: Rewrite `SKILL.md` as the Compact Executable Router

**Files:**
- Modify: `categories/workflow/unified-dev-flow/SKILL.md:10-113`
- Test: `categories/workflow/unified-dev-flow/scripts/test_router_policy.py`

**Interfaces:**
- Consumes: detailed rules from `references/policy-model.md`; existing stage and cross-cutting skill names.
- Produces: a compact agent-facing sequence with one route composition result and exactly one active Controller.

- [ ] **Step 1: Replace the overview and pre-routing sequence**

Replace the current “Scale decides depth” and pre-classification Entry Gate ordering with:

```markdown
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

Before Entry Gate or policy resolution, inspect repository state, constraints,
tests, active workflow state, and available spec backends without writing files.
`.codegraph/` is project-local and optional: use it first only when it already
exists and project instructions require it; never initialize it here.

## Resume Gate

Resolve FRESH / MATCH / COMPATIBLE_DRIFT / CONFLICTING_DRIFT before creating a
new route. MATCH resumes the recorded controller and stage; compatible drift is
reconciled; conflicting drift invalidates the stale plan and returns to Entry Gate.
```

- [ ] **Step 2: Keep the four-section Entry Gate but change its proof semantics**

Retain the four headings required by the checker. Replace “failing test first” with:

```markdown
4. **验证计划** → S5: name the `proof_mode`, its baseline/reproduction or unmet
   acceptance evidence, and the exact commands that will prove the change.
```

Require file scope to come from R0 evidence and require `delivery_target` in the task-specific statement.

- [ ] **Step 3: Replace the mutually exclusive task table with policy composition**

The compact router must state:

```text
Route = Resume + Intent + Complexity + Risk + Domain + Delivery
```

List only the base routes by intent and direct readers to `references/policy-model.md` for detailed tables. State explicitly that `Bug + Micro + Security + Production` means light planning plus adversarial assurance plus production review, stopping at the authorized delivery target.

- [ ] **Step 4: Add the single Controller invariant and adapter rule**

Add exactly one heading or bold label containing `Controller Ownership Invariant`. Define one-owner execution and explicit persisted handoff. Classify `speckit-chain`, OpenSpec change flow, `executing-plans`, `autopilot`, `ralph`, `team`, and `figure-it-out` as controllers; classify dispatch helpers and the local pstack `swarm` as workers rather than OMC's retired alias.

Add `Spec Adapter Resolution` and keep the resolution summary compact. Do not route every medium/large task directly to `speckit-chain`, and remove `Large-feature one-shot`.

- [ ] **Step 5: Replace universal TDD and mutation wording**

Add `Proof Before Change`, retaining RED-first for bugs/features while delegating other intent-specific proof modes to the policy reference. Define assurance tiers as deterministic, adversarial, and real mutation testing; remove the claim that reviewer counter-cases are mutation testing.

- [ ] **Step 6: Repair review and delivery state transitions**

Encode `S6 → S4 → S5 → S6`, evidence invalidation after intersecting changes, independent reviewer inputs, and the three-round escalation. Change the S7 exit condition from `Merged, deployed` to `Fulfill delivery target`.

- [ ] **Step 7: Run the policy test**

```bash
python3 categories/workflow/unified-dev-flow/scripts/test_router_policy.py
```

Expected: no legacy `SKILL.md` marker failures; enforcement/map failures may remain until Task 4.

- [ ] **Step 8: Commit the compact router**

```bash
git add categories/workflow/unified-dev-flow/SKILL.md
git commit -m "refactor: make unified flow policy driven"
```

---

### Task 4: Align Enforcement Semantics and the Repository Workflow Map

**Files:**
- Modify: `categories/workflow/unified-dev-flow/references/enforcement.md:1-65`
- Modify: `WORKFLOW-MAP.md:1-180`
- Test: `categories/workflow/unified-dev-flow/scripts/test_router_policy.py`

**Interfaces:**
- Consumes: unchanged four-heading checker contract and the new policy vocabulary.
- Produces: documentation that agrees with `SKILL.md` without changing checker behavior or introducing a runtime.

- [ ] **Step 1: Update Entry Gate enforcement documentation**

Add a `R0 Read-only Recon` subsection before Contract stating that shell/read tools remain allowed and file-write tools remain blocked. State that the four-section artifact is written after R0 and that §4 records:

```text
proof_mode + baseline/reproduction/unmet acceptance + exact verification commands
```

Update the micro example to use a config/schema or typo-search proof without claiming every task starts with a failing unit test. Keep artifact path, session isolation, four headings, length threshold, scope validation, and adapters unchanged.

- [ ] **Step 2: Rewrite the workflow map overview and routing table**

Replace the scale-first overview with:

```text
R0 → Resume Gate → Entry Gate → Policy Resolution → Controller → selected S0–S8 stages
Policy Resolution = Resume + Intent + Complexity + Risk + Domain + Delivery
```

Replace the single task-type table with separate Intent Base Route, Complexity/Planning, Risk/Assurance, Domain Adapter, and Delivery Target tables. Update the S4–S7 descriptions to use Proof Before Change, deterministic/adversarial/mutation assurance, `S6 → S4 → S5 → S6`, and `Fulfill delivery target`.

Document Spec Adapter Resolution and constitution `ensure/read-only` semantics. Remove the stale statement that every medium feature runs a fixed five-step Spec Kit chain.

- [ ] **Step 3: Run static and mechanical tests**

```bash
python3 categories/workflow/unified-dev-flow/scripts/test_router_policy.py
python3 categories/workflow/unified-dev-flow/scripts/test_entry_gate_check.py
```

Expected: both exit `0`; the first prints `All router policy checks passed.`, and the second prints `All tests passed.`

- [ ] **Step 4: Commit aligned documentation**

```bash
git add categories/workflow/unified-dev-flow/references/enforcement.md WORKFLOW-MAP.md
git commit -m "docs: align unified flow gates and workflow map"
```

---

### Task 5: Validate, Sync, and Audit Generated Changes

**Files:**
- Modify through generator only: `SKILLS-INDEX.md`
- Modify through generator only: `GEMINI.md`
- Potential generated metadata update: `categories/workflow/unified-dev-flow/SKILL.md`
- Test: all phase-one verification commands

**Interfaces:**
- Consumes: completed phase-one source files.
- Produces: synced skill installations and a clean, reproducible verification record.

- [ ] **Step 1: Validate before sync**

```bash
python3 categories/workflow/unified-dev-flow/scripts/test_router_policy.py
python3 categories/workflow/unified-dev-flow/scripts/test_entry_gate_check.py
python3 categories/.system/skill-creator/scripts/quick_validate.py categories/workflow/unified-dev-flow
git diff --check
```

Expected: all commands exit `0`.

- [ ] **Step 2: Run repository synchronization**

```bash
./sync.sh
```

Expected: synchronization completes successfully for configured tools and regenerates repository indexes according to existing rules.

- [ ] **Step 3: Audit the generated diff**

```bash
git status --short
git diff --stat
git diff -- SKILLS-INDEX.md GEMINI.md categories/workflow/unified-dev-flow/SKILL.md
```

Expected: only policy-router source files and documented generated outputs differ. Any unrelated deletion, imported skill, backup, or local override remains excluded.

- [ ] **Step 4: Re-run the full evidence set after sync**

```bash
python3 categories/workflow/unified-dev-flow/scripts/test_router_policy.py
python3 categories/workflow/unified-dev-flow/scripts/test_entry_gate_check.py
python3 categories/.system/skill-creator/scripts/quick_validate.py categories/workflow/unified-dev-flow
git diff --check
```

Expected: all commands exit `0` after generated metadata changes.

- [ ] **Step 5: Commit generated outputs and final source state**

Stage only files proven to belong to this plan:

```bash
git add categories/workflow/unified-dev-flow/SKILL.md \
  categories/workflow/unified-dev-flow/references/enforcement.md \
  categories/workflow/unified-dev-flow/references/policy-model.md \
  categories/workflow/unified-dev-flow/scripts/test_router_policy.py \
  WORKFLOW-MAP.md SKILLS-INDEX.md GEMINI.md
git commit -m "chore: sync unified flow policy router"
```

- [ ] **Step 6: Report final evidence and remaining phase-two boundary**

Report the exact commit SHAs, verification exit summaries, generated files, and any intentionally preserved unrelated changes. State explicitly that Gate Kernel, unified ledger, and Herdr adapters remain phase two.
