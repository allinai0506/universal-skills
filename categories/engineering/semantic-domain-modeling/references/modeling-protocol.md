# Modeling Protocol

## Goal

Produce the smallest domain model that removes material ambiguity for the current work.

## Evidence hierarchy

Prefer:

1. approved business rules;
2. production-observed behavior;
3. executable tests;
4. current data/migrations;
5. implementation code;
6. historical comments and naming.

A lower-level source must not silently override a higher-confidence source.

## Object test

Treat something as a domain object when it has one or more of:

- stable identity;
- lifecycle;
- business ownership;
- business rules;
- meaningful relationships;
- actions that change it.

Do not create a domain object merely because a table/class exists.

## Relationship test

A relationship belongs in the domain model if changing it can change business behavior, ownership, permissions, lifecycle, traceability, or decisions.

## Minimum scope

The current change should define only the semantic neighborhood it touches:

- directly changed objects;
- objects whose invariants can be affected;
- authoritative sources used by the change;
- immediate upstream/downstream relations.

Avoid modeling unrelated domains.

## Evidence table

Use:

| Evidence | Location | Claim | Confidence | Conflict |
|---|---|---|---|---|
| Requirement | ... | ... | HIGH | NO |

If two HIGH-confidence sources conflict, stop and escalate.
