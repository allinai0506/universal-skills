# States, Actions, and Invariants

## State model

For each lifecycle-bearing object define:

- state name;
- semantic meaning;
- entry condition;
- legal outgoing transitions;
- terminal/non-terminal property.

A state name must imply a business guarantee, not merely that a technical job ran.

## Action model

For each action define:

- actor;
- target;
- inputs;
- preconditions;
- permission;
- state/data mutation;
- side effects;
- failure behavior;
- idempotency expectations where material.

## Invariant model

An invariant must be:

- business meaningful;
- independent of one UI/controller;
- enforceable or verifiable;
- testable where possible.

Bad invariant:

> The Submit button is disabled after archive.

Good invariant:

> Archived records cannot be mutated through any write path.

## Cross-entry enforcement

Check every path that can change the fact:

- UI/API;
- batch jobs;
- imports;
- message consumers;
- admin tools;
- migration scripts;
- agent actions.
