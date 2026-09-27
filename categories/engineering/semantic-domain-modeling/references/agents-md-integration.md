# AGENTS.md Integration

Recommended repository rule:

```md
## Domain semantics gate

Before implementing any business change:

1. Read `docs/domain-model.md`.
2. Identify execution mode: Greenfield or Brownfield.
3. Identify affected domain objects and canonical terms.
4. Confirm authoritative sources of truth.
5. Confirm legal state transitions and actions.
6. Confirm applicable domain invariants.
7. If Brownfield, also read when present:
   - `docs/semantic-conflicts.md`
   - `docs/source-of-truth.md`
   - `docs/semantic-migration-plan.md`
8. If Brownfield discovery has not passed its gate, remain READ_ONLY for business code and business data structures.
9. If any material semantic conflict is unresolved, stop and report `BLOCKED` or `UNVERIFIED`.
10. Only then inspect implementation details and modify code.

Do not infer intended business meaning from table names, DTOs, controller names, legacy fallbacks, historical code, or tests alone.
```

## Separation of concerns

`AGENTS.md` answers:

> How must an agent work in this repository?

Semantic domain artifacts answer:

> What does this business world mean now, what should it mean, and which facts are authoritative?

Do not duplicate the full domain model into `AGENTS.md`.

## Brownfield protection rule

For repositories with existing production behavior, add:

```md
When semantic-domain-modeling runs in Brownfield Mode, the first pass is discovery only. Do not modify business code, schemas, state machines, or business data structures until the Brownfield Discovery Gate passes.
```
