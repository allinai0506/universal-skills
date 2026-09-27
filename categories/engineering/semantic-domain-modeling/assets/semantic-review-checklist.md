# Semantic Review Checklist

## Shared

- [ ] No new undocumented synonyms for core concepts.
- [ ] No overloaded field/name introduced for different lifecycles.
- [ ] No derived/cache/projection/history source is treated as authority.
- [ ] No undocumented fallback becomes business behavior.
- [ ] New states are represented in the domain model.
- [ ] New actions respect declared preconditions and permissions.
- [ ] All affected invariants hold across every write path.
- [ ] Tests cover material state transitions and invariant failures.
- [ ] Domain documentation was updated if semantics changed.

## Brownfield

- [ ] Intended, Implemented, and Observed semantics were not conflated.
- [ ] As-Is evidence exists for the changed semantic area.
- [ ] The change implements an approved To-Be rule.
- [ ] The change maps to a documented migration step.
- [ ] A legacy/fallback path was not removed before callers and data dependencies were checked.
- [ ] Any temporary dual-read/dual-write/fallback has an exit criterion.
- [ ] No new code extends a deprecated alias or legacy source of truth.
- [ ] The first archaeology pass remained READ_ONLY.
