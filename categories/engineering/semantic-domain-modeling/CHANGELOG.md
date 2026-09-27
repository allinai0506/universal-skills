# Changelog

## 1.1.0

### Added

- First-class `Greenfield` and `Brownfield` execution modes.
- Brownfield `READ_ONLY` first-pass rule.
- Repository Archaeology protocol.
- Semantic Inventory and Evidence Inventory requirements.
- Mandatory separation of `Intended`, `Implemented`, and `Observed` semantics.
- Explicit `As-Is` and `To-Be` domain models.
- Brownfield companion artifacts:
  - `docs/semantic-conflicts.md`
  - `docs/source-of-truth.md`
  - `docs/semantic-migration-plan.md`
- Semantic Convergence / incremental migration protocol.
- Brownfield templates, validator rules, tests, and example.
- `init_domain_model.py --mode brownfield` support.
- Brownfield bundle validation.

### Changed

- Existing code is explicitly treated as evidence, not automatically business truth.
- Fallback/legacy behavior must be modeled before modification.
- Coding gate now blocks changes when Brownfield semantic archaeology is incomplete.

## 1.0.0

- Initial semantic-domain-modeling skill package.
