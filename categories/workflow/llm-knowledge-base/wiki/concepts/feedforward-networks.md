---
title: "Feedforward Networks in Transformers"
tags: [concept, transformer, ffn]
sources: ["raw/articles/attention-is-all-you-need.md"]
related:
  - "[[transformer-architecture]]"
  - "[[mixture-of-experts]]"
  - "[[attention-mechanism]]"
created: 2026-06-02
updated: 2026-06-02
---

# Feedforward Networks in Transformers

The feedforward network (FFN) in each transformer block is a two-layer MLP that processes each token independently. It is the "computation" counterpart to the attention "communication" step.

## Structure

```
FFN(x) = W_2 · GELU(W_1 · x + b_1) + b_2
```

Typically with a 4x hidden dimension expansion (e.g., d_model=768 → d_ff=3072).

## The FFN-MoE Connection

The FFN is the natural insertion point for MoE in transformers:

1. **Each FFN unit ≈ mini-expert**: Individual neurons in the FFN hidden layer exhibit specialization — different neurons activate for different input patterns (syntactic, semantic, positional).

2. **MoE replaces the FFN with multiple expert FFNs**: The standard approach (Switch Transformer, Mixtral, DeepSpeed-MoE) replaces each FFN sublayer with N expert FFNs + a router.

3. **Sparsity spectrum**: From fully dense FFN → top-k activated expert FFNs → ReLU-activated sparse FFN neurons — there's a continuum of sparsity.

## Why FFN Is the Right MoE Target

- FFNs account for ~2/3 of transformer parameters
- Attention requires dense cross-token communication
- FFN processes tokens independently (embarrassingly parallel for expert dispatch)
- FFN specialization naturally emerges even without MoE routing
