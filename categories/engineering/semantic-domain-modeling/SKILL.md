---
name: semantic-domain-modeling
description: Align domain semantics before coding by defining shared terminology, core objects, relationships, states, actions, invariants, and authoritative sources of truth. Supports both Greenfield and Brownfield repositories. In Brownfield mode, first reconstruct Intended, Implemented, and Observed semantics in READ_ONLY discovery before any business-code change.
---

# Semantic Domain Modeling

## Purpose

Create and maintain a **Minimum Viable Ontology (MVO)** so humans, AI agents, tests, databases, APIs, and runtime behavior share the same business meaning.

Core rule:

> Never code before the affected domain semantics are aligned.

This is not a long prompt. It is an execution protocol with artifacts, evidence rules, gates, deterministic validation, and failure conditions.

The skill supports two first-class execution modes:

1. **Greenfield Mode** — define semantics before implementing a new repository/module.
2. **Brownfield Mode** — reconstruct and converge semantics in an existing repository without assuming current code is correct.

## Why This Skill Exists

Many software defects begin before code is written. They begin when humans, agents, tables, APIs, and services use the same words differently or use different words for the same business fact.

Typical failure chain:

```text
Ambiguous business concept
→ local code interpretation
→ duplicated source/state/rule
→ patch/fallback
→ more semantic drift
→ recurrent bug
```

The skill changes the order:

```text
Business evidence
→ shared semantics
→ explicit domain model
→ source/state/action/invariant gate
→ planning
→ coding
→ verification
```

## When to Use

Use before implementation when any of the following is true:

- a new repository or product is being created;
- a new core business module is introduced;
- a feature crosses module/service boundaries;
- the same business concept appears under multiple names;
- one object/fact has multiple candidate data sources;
- state transitions or lifecycle rules are non-trivial;
- multiple agents will work on the same business problem;
- a bug has recurred or previous fixes treated symptoms;
- fallback/legacy/compatibility logic obscures the authoritative path;
- a refactor changes concepts, ownership, lifecycle, actions, or source of truth;
- an existing repository began without explicit semantic alignment;
- agents must reverse-engineer business meaning from code.

## When NOT to Use

Do not force a full modeling pass for:

- pure copy or styling changes;
- local mechanical refactors that preserve business semantics;
- infrastructure-only changes with no domain meaning;
- generated-code refreshes with unchanged domain contracts.

If uncertain, run the Entry Gate. If no semantic risk exists, return `NOT_REQUIRED`.

# 1. Execution Mode Selection

Determine mode before any implementation work.

## Greenfield Mode

Use when the affected domain is not yet implemented or the repository/module is new.

Sequence:

```text
Requirements
→ Glossary
→ Objects
→ Relationships
→ States
→ Actions
→ Invariants
→ Sources of Truth
→ Semantic Handoff
→ Coding Gate
```

Primary artifact:

`docs/domain-model.md`

Initialize:

```bash
python scripts/init_domain_model.py /path/to/repo --mode greenfield
```

## Brownfield Mode

Use when code, schemas, runtime behavior, legacy paths, or production data already exist.

Sequence:

```text
Repository Archaeology
→ Evidence Inventory
→ Semantic Inventory
→ Conflict Detection
→ Intended / Implemented / Observed split
→ As-Is Model
→ To-Be Model
→ Source-of-Truth Decision
→ Semantic Migration Plan
→ Brownfield Discovery Gate
→ Controlled Migration / Coding
```

**First execution is READ_ONLY for business code and business data structures.**

Do not fix, rename, migrate, refactor, or normalize business behavior during semantic discovery.

Initialize:

```bash
python scripts/init_domain_model.py /path/to/repo --mode brownfield
```

Brownfield creates these artifacts without overwriting existing files:

```text
docs/domain-model.md
docs/semantic-conflicts.md
docs/source-of-truth.md
docs/semantic-migration-plan.md
```

Read `references/brownfield-archaeology.md` before Brownfield discovery and `references/semantic-migration.md` before any migration step.

# 2. Scope

This skill owns:

1. glossary and canonical terminology;
2. core domain objects and identities;
3. meaningful relationships;
4. lifecycle states and legal transitions;
5. business actions and pre/postconditions;
6. domain invariants;
7. authoritative sources of truth and non-authoritative copies;
8. semantic conflict detection;
9. Brownfield As-Is and To-Be models;
10. semantic migration/convergence constraints;
11. downstream semantic handoff for planning/coding/review agents.

This skill does **not** own detailed API design, database physical design, UI design, implementation planning, or coding.

# 3. Evidence Policy

Use the strongest available evidence.

Recommended hierarchy:

1. approved business requirements, policies, regulations, signed contracts, authoritative domain-owner decisions;
2. approved domain documentation and glossary;
3. observed production/runtime behavior and incident evidence;
4. tests that encode verified business behavior;
5. database migrations/schemas and persisted data shape;
6. domain models, services, APIs, workflows, enums;
7. recent PRs, fallback paths, comments, legacy compatibility code.

Important:

> Existing code is evidence, not automatically truth.

For Brownfield, keep three evidence/model categories separate:

- **Intended Model** — what the business should mean.
- **Implemented Model** — what repository code currently encodes.
- **Observed Behavior** — what actually happens at runtime.

Do not collapse them until evidence supports convergence.

# 4. Entry Gate

Before modeling, answer:

- Are core terms ambiguous, overloaded, or inconsistent?
- Are there competing names for one concept?
- Are there multiple technical representations of one object?
- Is the authoritative source unclear?
- Are lifecycle/state transitions involved?
- Are business invariants implicit?
- Will multiple agents/modules interpret the same concept?
- Is there fallback/legacy behavior?
- Is the repository already running without an explicit domain model?

If all answers are `NO`, record `NOT_REQUIRED` and stop.

If any answer is `YES` or `UNKNOWN`, continue.

# 5. Required Semantic Dimensions

Every affected scope must explicitly address these seven dimensions:

1. **Glossary**
2. **Objects**
3. **Relationships**
4. **States**
5. **Actions**
6. **Invariants**
7. **Sources of Truth**

Brownfield additionally requires:

8. **Evidence Inventory**
9. **Semantic Inventory**
10. **Intended / Implemented / Observed distinction**
11. **As-Is Model**
12. **To-Be Model**
13. **Semantic Conflicts**
14. **Semantic Migration Plan**

# 6. Core Procedure — Both Modes

## Phase 1 — Evidence Inventory

Collect evidence relevant to the requested scope only.

Use a table:

| Evidence | Location | What it claims | Confidence | Conflict? |
|---|---|---|---|---|

Do not silently choose one source when evidence conflicts.

## Phase 2 — Build the Glossary

For every important term define:

- canonical business name;
- code name;
- exact meaning;
- what it is not;
- aliases / forbidden aliases;
- bounded context where relevant.

One concept should have one canonical name inside a bounded context.

Read `references/modeling-protocol.md` and `references/semantic-conflicts.md`.

## Phase 3 — Identify Core Objects

For each core object define:

- identity;
- business meaning;
- lifecycle;
- owner/bounded context;
- authoritative source;
- derived/cache/projection/history representations.

Do not equate a database table with a business object without evidence.

## Phase 4 — Define Relationships

Define business relationships, not only foreign keys.

For each important relation state:

- source object;
- relationship verb;
- target object;
- cardinality when material;
- ownership/lifecycle implications;
- deletion/retention implications when material.

## Phase 5 — Define States

For lifecycle-bearing objects define:

- legal states;
- initial state;
- terminal states;
- legal transitions;
- forbidden transitions;
- actor/action that triggers transitions;
- transition preconditions.

Do not infer the intended state machine from scattered conditionals and then present it as truth.

Read `references/state-actions-invariants.md`.

## Phase 6 — Define Actions

A domain model for agentic software must model verbs, not only nouns.

For each core action define:

- actor;
- target object;
- inputs;
- preconditions;
- state/data change;
- side effects;
- permission boundary;
- success result;
- failure behavior.

## Phase 7 — Define Invariants

Write implementation-independent facts that must remain true across all entry points.

Examples:

- archived records cannot be mutated directly;
- every scoring criterion must be traceable to source text;
- only one active tender document may exist for a project;
- a derived value cannot override authoritative data.

An invariant is not satisfied by UI validation alone.

## Phase 8 — Declare Sources of Truth

For every critical fact answer:

> If two representations disagree, which one wins?

Classify each representation as:

- `AUTHORITATIVE`
- `DERIVED`
- `CACHE`
- `PROJECTION`
- `HISTORICAL`
- `EXTERNAL`
- `UNKNOWN`

Read `references/source-of-truth.md`.

## Phase 9 — Detect Semantic Conflicts

Explicitly scan for:

- synonym collisions;
- same-name/different-meaning fields;
- business object vs DB record vs binary file vs parsed text confusion;
- state vs asynchronous task-result confusion;
- source-of-truth ambiguity;
- hidden fallback semantics;
- duplicated lifecycle models;
- conflicting invariants;
- duplicate rules in Controller/Service/SQL/UI;
- legacy paths that can still create or mutate authoritative facts.

Every unresolved material conflict becomes `BLOCKED` or `UNVERIFIED`. Never guess.

# 7. Brownfield Procedure

Brownfield is not "run the Greenfield procedure against old code." It has its own discovery protocol.

## Brownfield Phase A — Repository Archaeology

First run is READ_ONLY.

Inspect relevant:

```text
README / AGENTS.md / docs
database migrations / schema
entities / aggregates / DTOs / VOs
enums / state transition logic
services / APIs / jobs / workflows
tests / fixtures
recent PRs and bug history
fallback / legacy / compatibility paths
production logs / incidents / observed data when available
```

Questions to answer:

- Where is each object created?
- Where is it mutated?
- Who reads it?
- Who can delete/archive it?
- Where do states change?
- Which path writes the critical fact?
- Which path reads the critical fact?
- Are there old and new paths simultaneously?
- Are fallbacks masking missing or contradictory facts?

Do not modify business code during this phase.

## Brownfield Phase B — Semantic Inventory

List names that may refer to the same or related concepts.

Classify each:

- `CANONICAL_CANDIDATE`
- `ALIAS`
- `LEGACY_ALIAS`
- `TECHNICAL_REPRESENTATION`
- `POSSIBLE_DUPLICATE`
- `UNKNOWN`

Do not rename code yet.

## Brownfield Phase C — Separate Intended / Implemented / Observed

For every material contradiction, record:

### Intended
What approved business evidence says should happen.

### Implemented
What code/schema/tests currently encode.

### Observed
What runtime, incidents, logs, persisted data, or user-visible behavior demonstrate.

A difference between these categories is a finding, not noise.

## Brownfield Phase D — Build As-Is Model

The As-Is model describes current reality, including undesirable behavior.

For material concepts include:

- current names;
- current technical representations;
- current read path;
- current write path;
- current state/lifecycle behavior;
- current fallback/legacy behavior;
- current authority ambiguity;
- known operational consequences.

Do not rewrite history into a clean model.

## Brownfield Phase E — Build To-Be Model

Only after As-Is is grounded, define the target:

- canonical terminology;
- canonical object boundaries;
- canonical relationships;
- explicit state machines;
- explicit business actions;
- explicit invariants;
- one authority for each critical fact;
- derived/cache/projection/history classifications;
- deprecated aliases/paths;
- intentional compatibility requirements.

## Brownfield Phase F — Create Companion Artifacts

Required:

```text
docs/semantic-conflicts.md
docs/source-of-truth.md
docs/semantic-migration-plan.md
```

`semantic-conflicts.md` must list evidence-backed contradictions.

`source-of-truth.md` must define authority and conflict rules for critical facts.

`semantic-migration-plan.md` must convert As-Is → To-Be into small verifiable migration steps.

## Brownfield Phase G — Brownfield Discovery Gate

Before any business-code modification, all must be true:

- [ ] Evidence Inventory exists for affected scope.
- [ ] Semantic Inventory exists for affected scope.
- [ ] Intended / Implemented / Observed are separated.
- [ ] Material conflicts are recorded.
- [ ] As-Is model is grounded in evidence.
- [ ] To-Be model is defined or explicitly `BLOCKED`.
- [ ] Critical facts have VERIFIED source-of-truth decisions or are `BLOCKED`.
- [ ] Semantic migration plan exists.
- [ ] The first discovery pass did not mutate business code or business data structures.
- [ ] No unresolved contradiction is being hidden by a code patch.

If any critical item is missing, remain in READ_ONLY mode.

Validate the Brownfield bundle:

```bash
python scripts/validate_domain_model.py /path/to/repo/docs/domain-model.md --mode brownfield --bundle
```

# 8. Semantic Migration / Convergence

Only after Brownfield Discovery Gate passes may migration/coding begin.

Read `references/semantic-migration.md`.

Preferred migration strategy:

```text
Freeze canonical semantics
→ New code obeys To-Be model
→ Stop creating new legacy paths
→ Add consistency observability
→ Introduce adapters where necessary
→ Migrate read paths
→ Migrate write paths
→ Reconcile/backfill data when required
→ Retire fallback
→ Delete deprecated semantics
```

This is **Semantic Convergence**.

Default is incremental migration, not a big-bang rewrite.

Every migration step must state:

- current semantic problem;
- target semantic rule;
- affected scope;
- compatibility requirement;
- verification method;
- rollback/containment strategy;
- legacy exit criterion.

# 9. Bug-Fix Mode

When invoked for a bug, begin with:

> Which domain fact is wrong?

Do not begin with:

> Which line should be patched?

Trace:

```text
Observed wrong behavior
→ Expected domain fact
→ Intended vs Implemented vs Observed difference
→ Broken object / relation / state / action
→ Violated invariant
→ Wrong or ambiguous source of truth
→ Root cause
→ Semantic decision
→ Implementation fix
```

Do not approve a symptom patch whose domain cause remains unexplained.

Fallback/retry/null handling/special cases are not root-cause fixes unless evidence shows they implement the correct domain rule.

# 10. Multi-Agent Rule

All participating agents must consume the same canonical semantic artifacts.

Recommended repository contract:

```text
AGENTS.md

docs/
  domain-model.md
  semantic-conflicts.md          # Brownfield when applicable
  source-of-truth.md             # Brownfield when applicable
  semantic-migration-plan.md     # Brownfield when applicable
```

`AGENTS.md` defines **how agents work**.

Semantic artifacts define **what the business world means**.

No agent may privately redefine a core term, source of truth, state, or invariant inside its own implementation.

Read `references/multi-agent-alignment.md` and `references/agents-md-integration.md`.

# 11. Downstream Handoff

After semantic alignment, produce a concise handoff using `assets/semantic-handoff.template.md`.

It must include:

- execution mode;
- affected objects;
- canonical terms;
- relevant relationships;
- legal states/transitions;
- actions;
- invariants;
- sources of truth;
- forbidden assumptions;
- unresolved/blocked items;
- Brownfield migration step if applicable.

Coding agents must treat this handoff as an implementation constraint, not background reading.

# 12. Mandatory Rules

1. **Semantics before implementation.** Do not code while an affected material semantic conflict is unresolved.
2. **Evidence before assumption.** Existing names and code paths are hypotheses until verified.
3. **One concept, one canonical name.** Aliases must be documented and intentionally retained or deprecated.
4. **One fact, one authority.** Multiple copies are allowed; multiple silent authorities are not.
5. **States are domain facts.** Do not derive the target state machine from scattered conditionals alone.
6. **Actions are part of the model.** Noun-only models are incomplete for agentic systems.
7. **Invariants cross entry points.** UI validation alone never satisfies a domain invariant.
8. **Fallback is not automatically a business rule.** Undocumented fallback is a risk until proven intentional.
9. **Unknown means unknown.** Use `UNKNOWN`, `UNVERIFIED`, or `BLOCKED`; never fabricate.
10. **Minimum viable scope.** Do not build an enterprise-wide ontology unless required.
11. **Brownfield first pass is READ_ONLY.** No business-code or business-data-structure mutation during archaeology.
12. **Code is not automatically truth.** Brownfield must separate Intended, Implemented, and Observed semantics.
13. **As-Is before To-Be.** Do not prescribe a clean target until current behavior is grounded.
14. **No semantic big-bang by default.** Use incremental Semantic Convergence.
15. **Every compatibility path needs an exit rule.** Temporary dual-read/dual-write/fallback must not become permanent by accident.

# 13. Verification Gate

## Greenfield Gate

Before completion:

- [ ] canonical terminology exists;
- [ ] core objects are defined;
- [ ] material relationships are defined;
- [ ] lifecycle states/transitions are explicit where applicable;
- [ ] core actions are explicit where applicable;
- [ ] invariants are explicit and implementation-independent;
- [ ] critical facts have declared sources of truth;
- [ ] semantic conflicts are resolved or blocked;
- [ ] downstream handoff is generated;
- [ ] validator passes.

Run:

```bash
python scripts/validate_domain_model.py /path/to/repo/docs/domain-model.md --mode greenfield
```

## Brownfield Gate

Before implementation/migration:

- [ ] all Greenfield semantic dimensions exist in To-Be scope;
- [ ] Evidence Inventory exists;
- [ ] Semantic Inventory exists;
- [ ] Intended / Implemented / Observed are separated;
- [ ] As-Is and To-Be models exist;
- [ ] material conflicts are recorded;
- [ ] source-of-truth decisions are explicit;
- [ ] migration plan exists;
- [ ] READ_ONLY discovery rule was respected;
- [ ] Brownfield bundle validator passes.

Run:

```bash
python scripts/validate_domain_model.py /path/to/repo/docs/domain-model.md --mode brownfield --bundle
```

# 14. Failure / Escalation

Return `BLOCKED` when:

- two authoritative business sources conflict;
- domain owners disagree on a material term/rule;
- source-of-truth ownership cannot be determined;
- legal state transitions are contradictory;
- an invariant conflicts with required behavior;
- Brownfield As-Is evidence is insufficient to safely define To-Be for the requested change;
- migration would destroy or reinterpret persisted business facts without an approved reconciliation rule.

Return `UNVERIFIED` when:

- evidence is incomplete;
- runtime behavior cannot be inspected;
- legacy paths appear authoritative but cannot be confirmed;
- a test encodes behavior whose business legitimacy is unknown.

Do not continue into coding by guessing.

# 15. Anti-Patterns

Reject these patterns:

### Code-first semantic inference

"The service does X, therefore X is the business rule."

Wrong in Brownfield without corroborating evidence.

### Table-equals-object

A DB table is a storage representation, not automatically a domain object.

### Fallback-as-fix

Adding another fallback to hide an unresolved source or lifecycle conflict.

### Multiple silent authorities

Two tables/services can independently write the same business fact without an explicit reconciliation rule.

### One overloaded status

A single `status` represents business state, parsing task state, approval state, and archive state.

### Private agent semantics

Each agent invents its own meaning for `Task`, `Document`, `Run`, `Project`, etc.

### Big-bang ontology rewrite

Trying to clean an entire mature repository in one semantic migration.

### Rename-before-identity

Renaming code before proving whether two names refer to the same object.

# 16. Progressive Loading

Load supporting files only when needed:

- base modeling → `references/modeling-protocol.md`
- naming/ambiguity → `references/semantic-conflicts.md`
- authority/data copies → `references/source-of-truth.md`
- lifecycle/actions/invariants → `references/state-actions-invariants.md`
- Brownfield discovery → `references/brownfield-archaeology.md`
- migration/convergence → `references/semantic-migration.md`
- multi-agent execution → `references/multi-agent-alignment.md`
- AGENTS.md integration → `references/agents-md-integration.md`
- Greenfield starter → `assets/domain-model.template.md`
- Brownfield starter → `assets/brownfield-domain-model.template.md`
- conflicts starter → `assets/semantic-conflicts.template.md`
- authority starter → `assets/source-of-truth.template.md`
- migration starter → `assets/semantic-migration-plan.template.md`
- coding handoff → `assets/semantic-handoff.template.md`
- review → `assets/semantic-review-checklist.md`

# 17. Examples

See:

- `examples/bid-system/domain-model.md`
- `examples/electronic-accounting-archive/domain-model.md`
- `examples/brownfield-bid-system/`

# 18. Completion Definition

The skill is complete only when a new human or agent, without historical chat context, can correctly answer for the affected scope:

1. What are the core business objects?
2. What does each mean and not mean?
3. How are they related?
4. What states can they be in?
5. What actions can change them?
6. What facts must never be violated?
7. Where is the authoritative value of each critical fact?

For Brownfield, they must additionally answer:

8. What did the repository actually do before alignment?
9. Which meanings came from Intended, Implemented, and Observed evidence?
10. What semantic conflicts remain?
11. What is the agreed To-Be model?
12. How will the repository converge without destabilizing production?

If the reader still needs to reverse-engineer these answers from code, semantic modeling is incomplete.

# Final Principle

> Code implements the model. Code does not define the model by itself.

For AI-native software:

> Shared semantics are infrastructure.

For mature software:

> Reconstruct reality before attempting to normalize it.
