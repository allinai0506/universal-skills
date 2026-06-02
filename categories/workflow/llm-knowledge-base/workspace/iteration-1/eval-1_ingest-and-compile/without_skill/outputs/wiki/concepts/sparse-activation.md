---
title: "Sparse Activation"
tags: [concept, efficiency, MoE, transformer]
sources:
  - "raw/articles/moe-2024.md"
related:
  - "[[Mixture of Experts: Scaling Transformer Models Beyond Dense Limits]]"
  - "[[Expert Routing]]"
  - "[[Soft MoE]]"
created: 2026-06-02
updated: 2026-06-02
---

# Sparse Activation

Sparse activation is a technique where only a subset of a model's parameters are activated for any given input token. This is the core efficiency mechanism behind Mixture of Experts architectures.

## Key Idea

Traditional dense models activate **all** parameters for every token. Sparse activation routes each token to a subset of "expert" sub-networks, so the total parameter count can be much larger than the active parameter count per token.

## Metrics

- **Sparse activation ratio**: The fraction of total parameters that activate per token. Lower is better for inference efficiency.
  - Pre-2024 MoE: ~30-35% active per token
  - Google 2024 breakthrough: ~10% active per token (3x improvement)

## Techniques to Increase Sparsity

1. **Dynamic expert selection**: Compatibility scoring between tokens and expert representations rather than a learned router.
2. **Expert specialization pressure**: Auxiliary loss that encourages experts to develop distinct specializations without explicit capacity constraints.
3. **Staged training**: Train in dense mode first, then progressively increase sparsity.

## Trade-offs

- **Pro**: Dramatically lower inference cost per token.
- **Con**: All expert weights must remain in memory, so memory footprint remains large.
- **Con**: Harder to fine-tune; risk of expert collapse and catastrophic forgetting.
