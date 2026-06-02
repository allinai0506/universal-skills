---
title: "Load Balancing in MoE"
tags: [concept, moe, routing, efficiency]
related:
  - "[[mixture-of-experts]]"
  - "[[expert-routing]]"
  - "[[top-k-routing]]"
  - "[[expert-collapse]]"
created: 2026-06-02
updated: 2026-06-02
---

# Load Balancing in MoE

Load balancing ensures that tokens are distributed roughly evenly across all experts in an MoE layer, preventing underutilization and ensuring stable training.

## The Problem

Without load balancing, the router tends to route most tokens to a few high-performing experts, causing:

- **Expert collapse**: Unused experts stop learning
- **Computational waste**: All expert weights must be kept in memory regardless of utilization
- **Training instability**: Uneven expert loads cause gradient magnitude variance

## Common Approaches

### Auxiliary Load Balancing Loss

Adds a penalty term that encourages uniform token distribution:

```
L_aux = α · Σ_i f_i · P_i
```

Where `f_i` is the fraction of tokens routed to expert i, and `P_i` is the average router probability for expert i.

### Expert Choice Routing

Instead of tokens choosing experts, experts choose tokens. This guarantees perfect load balance because each expert picks exactly its capacity worth of tokens.

### Soft MoE

Eliminates the load balancing problem entirely because each expert always processes the same number of slots regardless of token distribution.

### Batch-Aware Routing

Routing decisions are made with awareness of the batch-level distribution, not per-token.

## Trade-offs

| Method | Load Balance | Quality | Complexity |
|--------|-------------|---------|------------|
| Auxiliary loss | Good | Slight degradation | Low |
| Expert choice | Excellent | Good | Medium |
| Soft MoE | Perfect | Best | High |
| Batch routing | Very good | Good | Medium |

## Connections

- [[expert-collapse]] — What happens without load balancing
- [[expert-routing]] — Routing strategies including load-balanced variants
- [[mixture-of-experts]] — Core MoE architecture
