---
title: "Conditional Computation"
tags: [concept, efficiency, conditional]
sources: ["raw/articles/conditional-computation-review.md"]
related:
  - "[[mixture-of-experts]]"
  - "[[sparse-activation]]"
  - "[[attention-mechanism]]"
created: 2026-06-02
updated: 2026-06-02
---

# Conditional Computation

A paradigm where different parts of a neural network are activated conditionally based on the input — computing only what is needed for each example.

## Origins

Conditional computation dates back to early ensemble methods and adaptive mixture models. In deep learning, it was formalized by Bengio (2013) and popularized by the MoE layer in LSTMs (Shazeer et al., 2017, "Outrageously Large Neural Networks").

## MoE as Conditional Computation

MoE is the dominant form of conditional computation in modern LLMs. The router acts as a conditional gate:

```
if router(x) selects expert E_i:
    activate E_i(x)
else:
    skip E_i (zero computation)
```

## Attention as Conditional Computation

Attention is implicitly conditional — the weighted combination means tokens only use information from other tokens that are relevant. The softmax gate is a soft conditional computation:

```
attention_weight ≈ 0 → no information flows
attention_weight ≈ 1 → full information flows
```

## Toward Unified Conditional Computation

The boundary between attention and MoE blurs when considering:
- **Sparse attention** uses hard top-k selection (like MoE)
- **Soft MoE** uses soft weighted combinations (like attention)
- **Conditional attention** routes queries to specific key-value subsets

## Key Papers

- Bengio et al. (2013): "Estimating or Propagating Gradients Through Stochastic Neurons"
- Shazeer et al. (2017): "Outrageously Large Neural Networks"
- Recent conditional computation surveys connect both attention and MoE paradigms
