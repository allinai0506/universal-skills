# Normalization and Denormalization

Neither is universally correct.

## Prefer normalization when

- correctness of shared facts is important;
- writes are frequent;
- duplicated data is hard to synchronize;
- the workload does not justify duplication.

## Consider denormalization when

- a demonstrated high-value read path repeatedly performs expensive work;
- the workload justifies another representation;
- the consistency model is acceptable;
- update and rebuild mechanisms are explicit.

Before denormalization document:

```text
Read benefit
Write cost
Consistency risk
Storage cost
Rebuild strategy
```

If these cannot be stated, the optimization is not sufficiently justified.
