---
title: "MoE Scaling Properties"
tags: [concept, scaling, moe, efficiency]
related:
  - "[[scaling-laws]]"
  - "[[mixture-of-experts]]"
  - "[[sparse-activation]]"
created: 2026-06-02
updated: 2026-06-02
---

# MoE Scaling Properties

MoE architectures exhibit different scaling behavior than dense models because total parameters and compute-per-token are decoupled.

## Key Scaling Dimensions

### Total vs. Active Parameters

| Model | Total Params | Active per Token | Ratio |
|-------|-------------|------------------|-------|
| Mixtral 8x7B | 46.7B | 12.9B | 3.6x |
| Switch Transformer (2048 experts) | ~1.6T | ~0.8B | 2000x |

### Three Scaling Variables

MoE introduces an additional scaling axis compared to dense models:

1. **Expert count (E)**: More experts = more total capacity
2. **Active expert count (k)**: More active experts = more compute per token
3. **Expert capacity**: How many tokens each expert processes

### Scaling Law Modification

The Chinchilla scaling laws (Hoffmann et al., 2022) assume a fixed compute-to-parameter ratio. MoE violates this assumption: the "effective parameter count" for scaling purposes is the **active** parameter count, not the total.

This means:
- MoE can achieve dense-model-quality with fewer FLOPs
- The compute-optimal regime shifts: more total parameters for the same compute budget
- Diminishing returns set in when expert count grows beyond a point (empirically ~64 experts)

## Open Questions

- What is the optimal ratio of total to active parameters given a fixed inference budget?
- Do the scaling law exponents differ between dense and MoE models?
- How do you scale MoE to >10T total parameters efficiently?

## Connections

- [[scaling-laws]] — General scaling law theory
- [[mixture-of-experts]] — Core MoE concept
- [[sparse-activation]] — Sparse activation paradigm
