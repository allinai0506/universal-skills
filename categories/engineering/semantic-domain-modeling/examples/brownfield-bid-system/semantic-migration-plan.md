# Semantic Migration Plan — Brownfield Bid System

> Mode: BROWNFIELD
> Status: EXAMPLE_APPROVED

## Migration Principles

- No big-bang rewrite.
- New code follows To-Be semantics immediately.
- No new legacy metadata authority or undocumented fallback.
- Compatibility paths require observability and an explicit removal criterion.

## Steps

| Step | Class | Current Problem | Target Rule | Scope | Compatibility | Verification | Exit / Removal Criterion | Status |
|---|---|---|---|---|---|---|---|---|
| SM-001 | DOC_ONLY | terms and authority are implicit | freeze canonical terms and authority | docs/AGENTS | none | semantic review | downstream agents use same names | PLANNED |
| SM-002 | READ_PATH | resolver may read legacy metadata | resolve current tender from authoritative project metadata | scoring resolver | log legacy-only cases | integration tests + runtime metrics | zero legitimate legacy-only reads for agreed period | PLANNED |
| SM-003 | WRITE_PATH | multiple paths may create tender metadata | one write owner | upload/project document service | adapter for old API | contract tests | all new writes use authoritative path | PLANNED |
| SM-004 | DEPRECATION | historical fallback can hide missing current data | fallback becomes explicit error or approved historical lookup | scoring flow | temporary feature flag if required | incident regression tests | no required callers depend on fallback | PLANNED |
| SM-005 | REMOVAL | legacy semantics remain reachable | remove deprecated path | legacy services | only after evidence | full regression + production observation | legacy callers = 0 | PLANNED |
