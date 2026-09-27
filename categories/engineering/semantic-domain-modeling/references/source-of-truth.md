# Source of Truth Protocol

## Core question

For every critical business fact:

> If two representations disagree, which one is authoritative?

## Classifications

### AUTHORITATIVE
The canonical business truth for the fact.

### DERIVED
Computed from authoritative facts. It can be rebuilt.

### CACHE
Performance copy. Never wins against authority.

### PROJECTION
Read model optimized for a consumer. Rebuildable.

### HISTORICAL
Past snapshot/audit record. It describes history, not current truth unless explicitly queried as history.

### EXTERNAL
Owned by another system. Local storage may be a synchronized copy; ownership must be explicit.

## Required fields

For each critical fact record:

- fact;
- authoritative source;
- owner;
- write path;
- readers;
- synchronization/derivation rule;
- stale-data behavior;
- conflict resolution.

## Anti-patterns

Reject unless explicitly designed:

- dual writable masters;
- “use whichever is non-null”;
- old snapshot used as live fallback;
- search index treated as authority;
- UI state used as domain truth;
- AI output persisted as truth without validation.
