---
name: access-pattern-driven-data-modeling
description: Use when designing or changing a database schema, data model, index, query path, read model, or denormalized structure.
---

# Access Pattern Driven Data Modeling

## Overview

Design data models from the way data is actually accessed.

**Core rule:** Do not design the production data model first and discover access patterns later. Start from the operations the system must perform, then choose the data representation that supports those operations while preserving correctness.

## When to Use

- Creating or changing tables, collections, fields, or relationships
- Adding or changing indexes
- Designing list, search, detail, dashboard, or reporting queries
- Introducing denormalization, materialized views, or read models
- Investigating data-access performance
- Choosing between multiple persistent data representations

## When NOT to Use

- UI-only changes with no data-access impact
- Documentation-only changes
- Purely local in-memory structures
- Refactoring that demonstrably does not change persistence or query behavior

## Quick Reference

| Step | Action | Output |
|------|--------|--------|
| 1 | Identify concrete operations | Descriptions of observable system behavior |
| 2 | Build access-pattern inventory | Structured YAML with filters, sort, frequency, etc. |
| 3 | Identify dominant paths | Prioritized list of critical operations |
| 4 | Design simplest correct model | Normalization, indexes, partitioning decisions |
| 5 | Check write consequences | Trade-offs for denormalized/derived data |
| 6 | Validate critical queries | EXPLAIN plans, index usage, latency metrics |
| 7 | Validate growth behavior | 10x volume cost analysis |
| 8 | Produce decision record | Design rationale + verification evidence |

**Core Rules:**
1. **Access before Schema** — never derive schema only from entity classes
2. **Every nontrivial index has a reason** — map to a concrete operation
3. **Query shape matters** — predicates + column order + selectivity together
4. **Read optimization has a write cost** — make trade-off explicit
5. **Correctness before speed** — never violate invariants for performance
6. **Do not invent workload numbers** — use `UNKNOWN`
7. **Evidence beats intuition** — prefer executable plans and benchmarks
8. **Avoid premature complexity** — no sharding without workload evidence

## Implementation

### 1. Identify concrete operations

Describe observable system behavior before designing tables.

```
Bad:  "User entity"
Good: "Find the 20 most recent unpaid invoices for a customer, ordered by due date."
```

### 2. Build the access-pattern inventory

Record per operation (use `assets/access-patterns.example.yaml`):

| Field | Required? | Notes |
|-------|-----------|-------|
| name | ✅ | Unique identifier |
| type | ✅ | `read` or `write` |
| purpose | ✅ | Business context |
| filters | ✅ read only | Predicate columns |
| joins | - | Joined tables |
| sort | - | Columns + direction |
| returned_fields | - | Projection |
| pagination | - | Mode + size |
| frequency | ✅ | `high` / `medium` / `low` |
| expected_result_size | ✅ | e.g. `"<=20"`, `"1"` |
| expected_data_volume | - | `UNKNOWN` if unknown |
| freshness | - | `immediate` / `eventual` / N minutes |
| consistency | - | `strong` / `read-your-writes` / `eventual` |

**Inputs to collect, never invent unknown values — mark them `UNKNOWN`.**

Validate with:
```bash
python scripts/validate_access_patterns.py <your-inventory.yaml>
```

### 3. Identify dominant access paths

Prioritize by:
1. High-frequency operations
2. Latency-sensitive operations
3. Large-data operations
4. Primary user journeys
5. Repeatedly expensive operations

### 4. Design the simplest correct model

Only after step 3 decide on:
- normalization vs denormalization
- index definitions
- partitioning strategy
- precomputed / derived data
- materialized views or read models

**For every non-obvious decision, state which access pattern it serves.**

### 5. Check write consequences

For denormalized or derived data, determine:
- Update cost (how many writes, at what frequency?)
- Consistency risk (stale reads, anomaly windows)
- Failure behavior (partial updates, retries)
- Rebuild strategy (full recomputation, incremental)

If a second representation of business facts exists, ensure a derived-data rebuildability capability is available.

### 6. Validate critical queries

For important read paths:
1. Run the real or representative query
2. Use representative data volume (not dev-scale tiny)
3. Inspect the execution plan (`EXPLAIN`, `EXPLAIN ANALYZE`)
4. Verify intended indexes are **actually used** (not just defined)
5. Measure relevant latency / scan metrics
6. Compare evidence with the stated access pattern

> An index definition is not proof of usefulness.

### 7. Validate growth behavior

Ask: what happens at 10× data volume?

Identify cost growth type:
| Growth | Acceptable? |
|--------|-------------|
| Constant / logarithmic | ✅ |
| Scales with result size | Usually OK |
| Scales with scanned data | Watch out |
| Scales with total table size | ❌ Problem |

**Do not claim scalability from a tiny development dataset.**

### 8. Produce the decision record

Record:
- Access patterns considered
- Chosen data model
- Index / query decisions
- Rejected alternatives
- Trade-offs made
- Verification evidence
- Unresolved assumptions (`UNVERIFIED` items)

## Common Mistakes

| Mistake | Why bad | Fix |
|---------|---------|-----|
| **Entity-first modeling:** Design tables from application classes, then add indexes as an afterthought | Schema optimizes for "what entities exist" not "what operations need to run" | Reverse the order — enumerate operations first, then derive tables |
| **UI-first modeling:** One table per screen or page | Creates redundant data and consistency problems | The same entity is often accessed across multiple screens — shared model, per-screen query tuning |
| **Index-by-field:** Every frequently-mentioned column gets a single-column index | Wastes write I/O and storage; composite queries still need full scans | Design indexes for the actual predicate + sort shape of each operation |
| **Premature distributed design:** Add sharding or CQRS immediately for "future scale" | Adds enormous complexity before evidence of need | Start with single-instance + indexes; add complexity only when workload data proves it necessary |
| **Claim from tiny data:** "It's fast" tested on 100 rows | Linear scan on 100 rows ≠ linear scan on 10M rows | Test with representative volume or explicitly flag as `UNVERIFIED` |
| **Invent workload numbers:** Make up frequency/QPS/volume to fill in blanks | Decisions based on fake data produce wrong designs | Use `UNKNOWN` — the decision record will flag what evidence is missing |
| **Optimize correctness away:** Skip a join or constraint "for speed" | Silently violates business invariants, producing corrupt data | Preserve invariants first; find performance optimizations that don't break them |
| **Schema-only review:** Check DDL but never run the query | Indexes can exist but not be used; scan behavior can surprise | Always run `EXPLAIN` / query plan on representative data |

## Example

**Requirement:** `Show a customer's latest 20 unpaid invoices.`

**Access pattern:**
```text
type:          read
filters:       customer_id + status=unpaid
sort:          due_date DESC
result_size:   <=20
```

The agent must now verify whether the schema and **actual index choice** support this query efficiently — not add an index merely because `customer_id` exists as a column.

## Failure / Escalation

Return `UNVERIFIED` and stop making assumptions when:

- Critical access patterns are unknown
- Production-scale volume materially affects the decision but is unknown
- Consistency requirements are unclear
- A critical query cannot be reproduced
- The execution plan contradicts the intended access path
- A denormalized structure has no reliable update / rebuild strategy

**Report format:**
1. What is unknown
2. Why it matters (which decision is blocked)
3. What evidence is required to resolve it

## Deliverable

A completed task must provide:

1. Access-pattern inventory (YAML or equivalent structured form)
2. Data-model decision (tables, fields, relationships)
3. Index / query decisions (each mapped to an operation)
4. Important trade-offs (read vs write, consistency vs latency)
5. Verification evidence (query plans, benchmarks, measurements)
6. Known assumptions / `UNVERIFIED` items
