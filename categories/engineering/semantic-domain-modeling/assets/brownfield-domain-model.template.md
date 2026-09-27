# Domain Model

> Mode: BROWNFIELD
> Status: UNVERIFIED
> Discovery Rule: READ_ONLY until Brownfield Discovery Gate passes.

## Scope

<bounded scope of this semantic archaeology>

## Evidence Inventory

| Evidence | Location | Layer | What it claims | Confidence | Conflict? |
|---|---|---|---|---|---|
| <evidence> | <path/table/log> | Intended/Implemented/Observed | <claim> | HIGH/MEDIUM/LOW | yes/no |

## Semantic Inventory

| Name | Location | Classification | Meaning / Hypothesis | Status |
|---|---|---|---|---|
| <name> | <location> | CANONICAL_CANDIDATE/ALIAS/LEGACY_ALIAS/TECHNICAL_REPRESENTATION/POSSIBLE_DUPLICATE/UNKNOWN | <meaning> | UNVERIFIED |

## Intended Model

<what approved business evidence says should be true; use UNKNOWN when unavailable>

## Implemented Model

<what code/schema/tests currently encode>

## Observed Behavior

<what runtime/incidents/data demonstrate; use UNVERIFIED when unavailable>

## As-Is Model

### Glossary

| Canonical Candidate | Code Name(s) | Current Meaning | Not This | Aliases / Conflicts | Status |
|---|---|---|---|---|---|
| <term> | <code> | <meaning> | <not-this> | <aliases> | UNVERIFIED |

### Objects

| Object | Identity | Current Representations | Owner | Lifecycle | Current Authority | Status |
|---|---|---|---|---|---|---|
| <ObjectName> | <identity> | <db/api/file/text/etc> | <owner> | <lifecycle> | UNKNOWN | UNVERIFIED |

### Relationships

| Source | Relation | Target | Current Evidence | Status |
|---|---|---|---|---|
| <A> | <verb> | <B> | <evidence> | UNVERIFIED |

### States

| Object | State | Meaning | Legal From | Legal To | Evidence | Status |
|---|---|---|---|---|---|---|
| <Object> | <STATE> | <meaning> | <state> | <state> | <evidence> | UNVERIFIED |

### Actions

| Action | Actor | Target | Preconditions | Change | Side Effects | Evidence | Status |
|---|---|---|---|---|---|---|---|
| <Action> | <actor> | <object> | <precondition> | <change> | <effects> | <evidence> | UNVERIFIED |

### Invariants

- <invariant 1>

### Sources of Truth

| Fact | Current Candidate | Classification | Conflict Rule | Evidence | Status |
|---|---|---|---|---|---|
| <fact> | <source> | AUTHORITATIVE/DERIVED/CACHE/PROJECTION/HISTORICAL/EXTERNAL/UNKNOWN | <rule> | <evidence> | UNVERIFIED |

## To-Be Model

### Glossary

| Canonical Term | Code Name | Meaning | Forbidden / Legacy Aliases |
|---|---|---|---|
| <term> | <code> | <meaning> | <aliases> |

### Objects

| Object | Identity | Owner | Lifecycle | AUTHORITATIVE Source |
|---|---|---|---|---|
| <ObjectName> | <identity> | <owner> | <lifecycle> | <source> |

### Relationships

| Source | Relation | Target | Cardinality / Rule |
|---|---|---|---|
| <A> | <verb> | <B> | <rule> |

### States

| Object | State | Meaning | Legal From | Legal To |
|---|---|---|---|---|
| <Object> | <STATE> | <meaning> | <state> | <state> |

### Actions

| Action | Actor | Target | Preconditions | Result / State Change | Permission |
|---|---|---|---|---|---|
| <Action> | <actor> | <object> | <precondition> | <result> | <permission> |

### Invariants

- <invariant 1>

### Sources of Truth

| Fact | AUTHORITATIVE Source | Other Representations | Conflict Rule |
|---|---|---|---|
| <fact> | <source> | <derived/cache/etc> | authoritative wins |

## Semantic Conflicts

See `docs/semantic-conflicts.md`.

## Migration Direction

See `docs/semantic-migration-plan.md`.

## Discovery Gate

- [ ] Evidence inventory complete for current scope
- [ ] Semantic inventory complete for current scope
- [ ] Intended / Implemented / Observed separated
- [ ] Material conflicts recorded
- [ ] As-Is model grounded
- [ ] To-Be model defined or BLOCKED
- [ ] Critical sources of truth VERIFIED or BLOCKED
- [ ] Migration plan created
- [ ] Business code remains unchanged during discovery
