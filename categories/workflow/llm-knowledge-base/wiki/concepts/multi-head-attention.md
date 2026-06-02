---
title: "Multi-Head Attention"
tags: [concept, attention, parallel]
sources: ["raw/articles/attention-is-all-you-need.md"]
related:
  - "[[attention-mechanism]]"
  - "[[transformer-architecture]]"
  - "[[mixture-of-experts]]"
created: 2026-06-02
updated: 2026-06-02
---

# Multi-Head Attention

Multi-Head Attention (MHA) runs h parallel attention operations, each with different learned projections, and concatenates the results.

## Structure

```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) · W_O
where head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
```

## The Multi-Head / MoE Parallel

There is a striking structural parallel between multi-head attention and mixture of experts:

| Aspect | Multi-Head Attention | Mixture of Experts |
|--------|---------------------|-------------------|
| Number of units | h heads | E experts |
| Unit specialization | Different attention patterns | Different knowledge domains |
| Selection mechanism | All heads always active (dense) | Only top-k experts active (sparse) |
| Output combination | Concatenate + linear projection | Weighted sum via router |
| Training dynamics | Heads naturally specialize (known as "head collapse" when redundant) | Experts naturally specialize with load balancing loss |

## Key Insight

If you apply MoE-style sparsity to multi-head attention — only activating a subset of heads per token — you get sparse attention routing, which is exactly what several crossover works explore (see [[attention-moe-crossover]]).
