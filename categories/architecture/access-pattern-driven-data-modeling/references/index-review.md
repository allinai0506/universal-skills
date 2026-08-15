# Index Review

For every important index record:

```text
Index:
Table:
Columns:
Supporting operations:
Predicate shape:
Sort shape:
Expected selectivity:
Write overhead:
Storage overhead:
Actual execution plan:
Measured result:
```

Questions:

1. Which concrete query requires this index?
2. Does column order match the predicate/sort pattern?
3. Is the predicate selective enough?
4. Does the optimizer actually use it?
5. What write/storage cost does it add?
6. Could an existing index serve the same operation?
7. Does it remain useful as data distribution changes?

An index definition alone is not evidence.
