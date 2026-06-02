---
title: "MoE 2024 Breakthroughs"
tags: [article, moe, sparsity, efficiency]
sources: ["raw/articles/moe-2024.md"]
related:
  - "[[mixture-of-experts]]"
  - "[[sparse-activation]]"
  - "[[expert-routing]]"
created: 2026-06-02
updated: 2026-06-02
---

# MoE 2024 Breakthroughs

The 2024 breakthroughs in Mixture of Experts, centered on achieving a 3x sparse activation ratio.

## The 3x Sparse Activation Ratio

In 2024, Google achieved a breakthrough: only ~10% of parameters activate per token, compared to the previous ~30-35% in models like Mixtral.

### Key Techniques

1. **Dynamic expert selection**: Replaces the learned gating network with a compatibility score computed between each token and a learned expert representation. This is structurally similar to attention's QK^T computation.

2. **Expert specialization pressure**: An auxiliary loss that encourages experts to develop distinct specializations without imposing rigid capacity constraints. Analogous to the diversity losses used in some multi-head attention variants.

3. **Staged training**: The model is first trained in dense mode (all experts active), then sparsity is progressively increased. This allows experts to develop specializations before being asked to compete for tokens.

## Implications

- Enables much larger total parameter counts without proportional compute increase
- Moves MoE closer to the "infinite expert" limit
- Further blurs the line between attention and MoE routing

## Connections

- [[mixture-of-experts]] — Core concept
- [[sparse-activation]] — Activation sparsity
- [[attention-moe-crossover]] — Attention-inspired routing innovations
