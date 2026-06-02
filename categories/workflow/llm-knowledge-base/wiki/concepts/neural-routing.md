---
title: "Neural Routing"
tags: [concept, routing, gating]
sources: ["raw/articles/gating-and-routing-survey.md"]
related:
  - "[[mixture-of-experts]]"
  - "[[attention-mechanism]]"
  - "[[conditional-computation]]"
created: 2026-06-02
updated: 2026-06-02
---

# Neural Routing

The mechanism by which a neural network directs different inputs to different computational paths. Routing is the fundamental operation underlying both attention and mixture of experts.

## Routing in Attention

Attention routing determines which tokens information flows between:

```
Query Token → softmax(QK^T) → Weighted sum of Value tokens
```

This is **content-based routing** — routing decisions depend on the semantic content of both the query and key tokens.

## Routing in MoE

MoE routing determines which expert modules process each token:

```
Token → Router(x) → Top-k(softmax(W·x)) → Selected Experts
```

This is also **content-based routing** — the router uses the token's representation to decide which experts to dispatch to.

## The Deep Connection

Both attention and MoE solve the same fundamental problem: **which computation should be applied to which input?**

| Aspect | Attention Routing | MoE Routing |
|--------|-------------------|-------------|
| Granularity | Token → Token | Token → Expert module |
| Decision space | O(n) possible targets (n = sequence length) | O(E) possible targets (E = expert count) |
| Output | Weighted combination of values | Weighted combination of expert outputs |
| Differentiability | Fully differentiable (soft) | Discrete top-k (hard) or soft assignment |
| Training | Learned end-to-end | Learned end-to-end (+ auxiliary losses) |

## Crossover: Routing as a Unifying Framework

A growing body of work treats both attention and MoE as instances of a broader **learned routing** paradigm. See [[attention-moe-crossover]].
