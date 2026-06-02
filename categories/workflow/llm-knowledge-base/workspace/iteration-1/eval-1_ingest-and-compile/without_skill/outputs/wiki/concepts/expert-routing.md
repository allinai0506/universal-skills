---
title: "Expert Routing"
tags: [concept, MoE, routing, sparsity]
sources:
  - "raw/articles/moe-2024.md"
related:
  - "[[Mixture of Experts: Scaling Transformer Models Beyond Dense Limits]]"
  - "[[Sparse Activation]]"
  - "[[Soft MoE]]"
  - "[[Switch Transformer]]"
created: 2026-06-02
updated: 2026-06-02
---

# Expert Routing

Expert routing is the mechanism that determines which expert sub-networks process each token in a Mixture of Experts model. The routing strategy is a key architectural decision that affects both model quality and computational efficiency.

## Routing Strategies

### Hard Routing (top-k)
- Each token is dispatched to exactly k experts (usually k=1 or k=2).
- **Switch Transformer** uses top-1 routing, the simplest form.
- **Mixtral 8x7B** uses top-2 routing.
- Simple, efficient, but can cause load imbalance.

### Soft Routing
- Each token is a weighted combination of all experts.
- **Soft MoE** eliminates discrete routing entirely.
- Better gradient flow and no load balancing loss needed.
- Higher compute cost per token.

### Dynamic Expert Selection (Google 2024)
- Computes a compatibility score between each token and expert representation.
- Not a learned router — uses a scoring function instead.
- Part of the 2024 3x sparse activation ratio breakthrough.

## Challenges

- **Load balancing**: Without careful design, some experts receive most tokens while others starve.
- **Expert collapse**: Specialization can be fragile; unused experts stop learning.
