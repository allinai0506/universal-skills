---
title: "Top-K Routing"
tags: [concept, routing, moe, gating]
related:
  - "[[expert-routing]]"
  - "[[mixture-of-experts]]"
  - "[[soft-routing]]"
created: 2026-06-02
updated: 2026-06-02
---

# Top-K Routing

Top-K routing is the standard expert selection mechanism in MoE architectures: each token is routed to the top-K experts with the highest router scores.

## Definition

Given a router that computes scores for E experts:

```
scores = softmax(W_r · x)        # E-dimensional probability vector
indices = top-k(scores)          # Select k expert indices
output = Σ_i scores[i] · E_i(x)  # Weighted sum of k expert outputs
```

## Common Configurations

- **Top-1** (Switch Transformer): Each token activates exactly one expert. Simple but can cause severe load imbalance.
- **Top-2** (Mixtral 8x7B): Each token activates two experts. Balances quality and efficiency. Standard for production MoE.
- **Top-4+**: Used in very large MoE models. Improves quality but reduces sparsity benefit.

## Challenges

- **Load imbalance**: Tokents may cluster on a few experts
- **Expert collapse**: If an expert is never in the top-k, it receives no gradient
- **Auxiliary losses**: Load balancing and importance weighting losses are needed

## Connections

- [[expert-routing]] — Taxonomy of routing strategies
- [[soft-routing]] — The soft alternative (attention-like)
- [[mixture-of-experts]] — Core MoE concept
