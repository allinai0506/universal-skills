# Semantic Handoff

## Execution Mode

`GREENFIELD` or `BROWNFIELD`

## Scope

<What change this handoff covers.>

## Canonical Terms

- `<Term>` = <definition>

## Affected Objects

- `<Object>` — <meaning>

## Relationships

- `<A> -> <relation> -> <B>`

## States / Transitions

- `<STATE_A> -> <STATE_B>` allowed when <condition>
- `<STATE_X> -> <STATE_Y>` forbidden

## Actions

- `<Action>`: <actor>, <precondition>, <result>

## Invariants

1. <must remain true>

## Sources of Truth

- `<Fact>` → `<authoritative source>`

## Brownfield Migration Step

- `N/A` for Greenfield, otherwise reference the approved `SM-xxx` step.
- State whether the step changes READ_PATH / WRITE_PATH / STATE_MACHINE / DATA_MIGRATION / API_CONTRACT / DEPRECATION / REMOVAL.

## Forbidden Assumptions

- Do not treat <derived/cache/history> as authority.
- Do not assume <ambiguous concept> means <incorrect meaning>.
- In Brownfield, do not treat existing code as proof of intended business semantics.

## Open / Blocked

- `NONE` or list `UNKNOWN` / `UNVERIFIED` / `BLOCKED` items.

## Implementation Gate

Implementation may start only when material `BLOCKED` items in this step's blast radius are zero and, for Brownfield, the Discovery Gate has passed.
