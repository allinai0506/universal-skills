# Package Validation — v1.1.0

This package is valid only if structural, behavioral, and deterministic tests pass.

## Structural validation

Required root paths:

- `SKILL.md`
- `README.md`
- `VALIDATION.md`
- `references/`
- `scripts/`
- `assets/`
- `tests/`
- `examples/`

Brownfield support requires:

- `references/brownfield-archaeology.md`
- `references/semantic-migration.md`
- `assets/brownfield-domain-model.template.md`
- `assets/semantic-conflicts.template.md`
- `assets/source-of-truth.template.md`
- `assets/semantic-migration-plan.template.md`

## SKILL.md validation

`SKILL.md` must contain:

- YAML frontmatter with non-empty `name` and `description`;
- Greenfield and Brownfield mode selection;
- Purpose and scope;
- Entry Gate;
- seven core semantic dimensions;
- Brownfield Repository Archaeology;
- Intended / Implemented / Observed distinction;
- As-Is and To-Be requirements;
- Brownfield READ_ONLY rule;
- Semantic Migration / Convergence;
- Mandatory Rules;
- Verification Gates;
- Failure / Escalation;
- Progressive Loading.

## Behavioral validation

The skill must:

1. stop coding on unresolved material semantic conflicts;
2. distinguish authoritative, derived, cache, projection, historical, external, and unknown data;
3. require glossary, objects, relationships, states, actions, invariants, and source-of-truth definitions;
4. produce a downstream handoff;
5. include deterministic validation;
6. mark missing evidence as `UNKNOWN`, `UNVERIFIED`, or `BLOCKED`, never guessed;
7. treat existing code as evidence rather than automatic truth;
8. force Brownfield first pass to remain READ_ONLY;
9. separate Intended, Implemented, and Observed semantics;
10. require As-Is before To-Be;
11. require a semantic migration plan before Brownfield coding;
12. prefer incremental Semantic Convergence over big-bang rewrite.

## Deterministic tests

Run from the skill root:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

Expected: all tests pass.

## Greenfield validation

```bash
python scripts/validate_domain_model.py examples/bid-system/domain-model.md --mode greenfield
python scripts/validate_domain_model.py examples/electronic-accounting-archive/domain-model.md --mode greenfield
```

## Brownfield bundle validation

```bash
python scripts/validate_domain_model.py examples/brownfield-bid-system/domain-model.md --mode brownfield --bundle
```

Expected: `PASS`.
