# Brownfield Semantic Archaeology

Use this protocol for repositories that already contain production code, historical migrations, legacy paths, or established runtime behavior.

## Goal

Reconstruct the domain meaning from evidence before changing it.

Brownfield work is not "document what the code says." Existing code may contain drift, temporary compatibility logic, duplicated concepts, and historical mistakes.

The first execution is **READ_ONLY** for business code and data structures.

## Three Models That Must Stay Separate

### Intended Model
What approved requirements, policy, domain owners, or authoritative business documentation say the system should mean.

### Implemented Model
What the repository currently encodes in schemas, models, services, APIs, enums, workflows, and tests.

### Observed Behavior
What actually happens in runtime: production logs, incidents, persisted data, integration behavior, and user-visible outcomes.

Never collapse these three into one without evidence.

## Phase A — Repository Archaeology

Inspect relevant evidence only:

1. README / AGENTS.md / docs;
2. database migrations and schemas;
3. entities, aggregates, domain models, DTOs/VOs;
4. enums and state-transition logic;
5. services, APIs, jobs, workflow definitions;
6. tests and fixtures;
7. recent PRs and bug-fix history;
8. fallback, compatibility, legacy, and deprecated paths;
9. production logs/incidents when available.

For each claim, record:

| Claim | Evidence | Layer | Confidence | Contradiction |
|---|---|---|---|---|
| ... | file/table/log | Intended/Implemented/Observed | HIGH/MEDIUM/LOW | yes/no |

## Phase B — Semantic Inventory

Inventory all names used for important concepts.

Classify each finding:

- `CANONICAL_CANDIDATE`
- `ALIAS`
- `LEGACY_ALIAS`
- `TECHNICAL_REPRESENTATION`
- `POSSIBLE_DUPLICATE`
- `UNKNOWN`

Example:

| Name | Appears in | Classification | Possible meaning |
|---|---|---|---|
| TenderDocument | domain | CANONICAL_CANDIDATE | business document |
| TenderFile | API | POSSIBLE_DUPLICATE | unclear |
| project_documents | DB | TECHNICAL_REPRESENTATION | metadata record |
| OBS object | storage | TECHNICAL_REPRESENTATION | binary payload |

Do not rename code during discovery.

## Phase C — Conflict Detection

Explicitly search for:

- multiple authorities for one fact;
- one name used for different concepts;
- multiple names for one concept;
- object/file/record/text/result conflation;
- duplicated state machines;
- conflicting legal transitions;
- duplicated rules in controller/service/SQL/UI;
- hidden fallback behavior;
- legacy paths that can still write authoritative state;
- cache/projection/history accidentally treated as authority.

Every conflict must be recorded in `docs/semantic-conflicts.md`.

## Phase D — As-Is Model

Create the current factual model before proposing a target.

The As-Is model must say what the system does now, even if it is undesirable.

Required fields for material concepts:

- current names;
- current representations;
- current read path;
- current write path;
- current lifecycle/state behavior;
- current fallback/legacy behavior;
- current authority ambiguity;
- known production consequences.

Mark contradictions rather than smoothing them over.

## Phase E — To-Be Model

Only after the As-Is model is grounded may you define the target model.

The To-Be model must define:

- canonical terminology;
- canonical objects and relations;
- explicit states/actions/invariants;
- one authoritative source per critical fact;
- what becomes derived/cache/projection/history;
- what is deprecated;
- what remains intentionally compatible.

## Brownfield Discovery Gate

Before any business code modification, all must be true:

- [ ] evidence inventory exists;
- [ ] semantic inventory exists;
- [ ] material conflicts are listed;
- [ ] As-Is model exists;
- [ ] target To-Be model exists or is intentionally BLOCKED;
- [ ] critical sources of truth are determined or BLOCKED;
- [ ] migration plan exists;
- [ ] no unresolved contradiction is being hidden by a patch.

If any critical item is missing, remain in READ_ONLY mode.

## Hard Rules

1. Do not infer business truth solely from existing code.
2. Do not treat tests as authoritative if they conflict with approved business rules or observed production truth.
3. Do not use a fallback as proof of intended semantics.
4. Do not delete legacy behavior until its callers and persisted data are understood.
5. Do not normalize names until object identity and ownership are clear.
6. Do not perform a big-bang refactor as part of semantic discovery.
7. Unknown remains `UNKNOWN`, `UNVERIFIED`, or `BLOCKED`.
