# Refactoring Heuristics

These heuristics are derived from the engineering themes of *Clean Code*: meaningful names, small functions, single responsibilities, low duplication, readable control flow, disciplined error handling, clean tests, and incremental refinement.

They are heuristics, not absolute laws.

## Smells that justify investigation

- misleading or vague names;
- long functions with multiple abstraction levels;
- repeated logic that changes together;
- deeply nested conditionals;
- hidden side effects;
- functions with many unrelated arguments;
- comments explaining code that could be made self-evident;
- classes with unrelated responsibilities;
- tests that are difficult to understand or isolate.

## Refactoring response

Map each smell to the smallest transformation that addresses it.

| Smell | First transformation to consider |
|---|---|
| Vague name | Rename |
| Long coherent block | Extract function |
| Repeated logic | Extract shared behavior |
| Nested conditional | Guard clause / simplify condition |
| Mixed abstraction levels | Separate functions by abstraction level |
| Hidden side effect | Isolate side effect |
| Large class with unrelated concerns | Extract cohesive responsibility |
| Comment explaining mechanics | Improve names/structure |

Do not mechanically apply every heuristic.

## The Boy Scout principle

When touching code, leave the touched area at least as understandable as before, provided this does not expand the task beyond a reasonable scope.

The principle does not authorize unrelated cleanup.

## Behavior-preservation checklist

While refactoring, preserve every observable dimension of the contract:

- external contracts and public APIs;
- control-flow semantics;
- ordering where observable;
- exception/error behavior;
- null/empty handling;
- transaction boundaries;
- concurrency behavior;
- side effects;
- serialization/protocol formats.

## Simple design

A useful order of priorities is:

1. behavior is correct;
2. duplication is reduced;
3. intent is expressed clearly;
4. structure is kept as small and simple as practical.

Tests provide the feedback loop that makes incremental refinement safer.
