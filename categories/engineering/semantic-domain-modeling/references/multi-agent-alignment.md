# Multi-Agent Semantic Alignment

## Shared contract

All agents working on the same scope must read the same `docs/domain-model.md` before planning or coding.

No agent may privately redefine a core term in its own task prompt.

## Agent roles

### Requirement / Product Agent
May propose semantic changes but must mark them as proposed until accepted.

### Architecture Agent
Maps the accepted domain model to boundaries, interfaces, and storage; it must not redefine business meaning for convenience.

### Coding Agent
Implements the accepted model and reports mismatches rather than inventing rules.

### Test Agent
Derives tests from states, actions, invariants, and authority rules.

### Review Agent
Checks semantic drift as well as code correctness.

## Drift detection

Review should flag:

- new aliases not in glossary;
- new write paths to non-authoritative copies;
- new states outside the model;
- new fallback paths;
- invariant enforcement limited to one entry point;
- action behavior that differs across modules.

## Update protocol

When implementation reveals a genuine semantic gap:

1. stop the affected implementation;
2. update the domain model from evidence;
3. record the decision;
4. regenerate the handoff;
5. resume implementation.
