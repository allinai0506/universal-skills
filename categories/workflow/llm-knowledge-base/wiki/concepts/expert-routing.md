---
title: "Expert Routing"
tags: [concept, routing, MoE, gating]
# NOTE: This page intentionally has NO sources: field — missing provenance test case
related: ["[[Mixture of Experts]]", "[[Sparse Activation]]", "[[Soft MoE]]", "[[Top-K Routing]]"]
created: 2026-06-02
updated: 2026-06-02
---

# Expert Routing

Expert routing is the mechanism by which an MoE model decides which expert(s) should process each token. It is arguably the most important design decision in any MoE architecture.

## Routing Strategies

### Top-K Routing (Hard Routing)
The classic approach. The router computes scores for each expert and routes each token to the top-K experts. Switch Transformer uses top-1; Mixtral uses top-2.

- **Pro:** Simple, computationally efficient
- **Con:** Can lead to expert collapse and load imbalance

### Soft Routing (Soft MoE)
Each token is assigned a soft weight across all experts. Tokens are combined linearly before being processed by each expert, then the weighted outputs are aggregated.

- **Pro:** Better gradient flow, eliminates load balancing loss
- **Con:** Higher computational overhead

### Hierarchical Routing
Multiple levels of routing with expert groups at each level.

- **Pro:** Scales to massive expert counts
- **Con:** Complex to implement and tune

## Open Research Questions

The recently proposed [[Deep Routing]] approach shows promise for end-to-end learned routing policies, but is still experimental.

## Evaluation

Different routing strategies show different trade-offs on key metrics:

| Strategy | Load Balance | Compute Efficiency | Model Quality |
|----------|-------------|-------------------|---------------|
| Top-1 | Poor | Excellent | Good |
| Top-2 | Good | Good | Better |
| Soft | Excellent | Moderate | Best |
| Hierarchical | Good | Good | Good |
