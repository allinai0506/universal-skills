# Semantic Migration and Convergence

Use after Brownfield archaeology has produced a grounded As-Is model and an approved To-Be model.

## Goal

Move an existing repository toward one coherent semantic model without destabilizing production behavior.

This is **Semantic Convergence**, not a mandatory big-bang rewrite.

## Required Artifact

Create `docs/semantic-migration-plan.md`.

Each migration item must contain:

- current semantic problem;
- target semantic rule;
- affected code/data/interfaces;
- compatibility requirement;
- migration step;
- verification method;
- rollback or containment strategy;
- deletion criterion for legacy behavior.

## Migration Order

Prefer this order:

1. Freeze canonical terminology and To-Be model.
2. Make new code obey the To-Be model.
3. Prevent creation of new legacy paths.
4. Add observability and consistency checks.
5. Introduce adapters/mappers where necessary.
6. Migrate reads toward the authoritative source.
7. Migrate writes toward the authoritative source.
8. Backfill or reconcile historical data if required.
9. Remove fallback only after evidence proves it is no longer required.
10. Delete deprecated models/paths after callers are gone.

## Change Classes

Classify every step:

- `DOC_ONLY`
- `READ_PATH`
- `WRITE_PATH`
- `STATE_MACHINE`
- `DATA_MIGRATION`
- `API_CONTRACT`
- `DEPRECATION`
- `REMOVAL`

Higher-risk classes require stronger validation.

## Safety Rules

- One migration step should have one semantic purpose.
- Never change authority and state-machine semantics in the same unreviewed step unless inseparable.
- Prefer compatibility adapters over duplicated business logic.
- A temporary dual-read or dual-write strategy must have an explicit exit criterion.
- Any data backfill must be idempotent or have a deterministic recovery plan.
- New code must not introduce aliases that are absent from the canonical glossary.

## Migration Gate

Coding may begin only when:

- the affected To-Be semantics are VERIFIED;
- source-of-truth ownership is known;
- affected invariants are explicit;
- compatibility requirements are explicit;
- the step has a verification plan;
- unresolved conflicts are outside the step's blast radius or marked BLOCKED.

## Completion

Semantic migration is complete only when:

- canonical terms dominate new code and public contracts;
- deprecated aliases no longer create new data or behavior;
- critical facts have one authority;
- duplicate state machines are removed or formally separated;
- fallback behavior is either documented business behavior or eliminated;
- tests assert the domain model rather than legacy accidents.
