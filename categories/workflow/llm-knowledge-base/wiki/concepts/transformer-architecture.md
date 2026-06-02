---
title: "Transformer Architecture"
tags: [concept, architecture, foundation-model]
sources: ["raw/articles/attention-is-all-you-need.md", "raw/articles/moe-2024.md"]
related:
  - "[[attention-mechanism]]"
  - "[[mixture-of-experts]]"
  - "[[feedforward-networks]]"
  - "[[multi-head-attention]]"
created: 2026-06-02
updated: 2026-06-02
---

# Transformer Architecture

The transformer (Vaswani et al., 2017) is the foundational architecture that popularized attention as the primary computation primitive for sequence modeling.

## Architecture

```
Input → [Self-Attention → Add & Norm → FFN → Add & Norm] × N layers
```

Each transformer layer consists of:
1. **Multi-Head Self-Attention**: Tokens communicate with each other
2. **Feedforward Network (FFN)**: Each token is processed independently through a 2-layer MLP
3. **Residual connections + LayerNorm**: Stabilize training

## The Transformer as a Fusion Point

The transformer is where attention and MoE meet:

### The FFN as a Mini-MoE
The feedforward network in each transformer layer expands the representation by 4x (e.g., 768 → 3072 → 768). This expansion-and-compression pattern is conceptually similar to an MoE layer — the wide middle layer can be seen as a set of "hidden expert units" that are activated by different input patterns.

### When MoE Replaces the FFN
The standard MoE-in-transformer pattern (Shazeer et al., 2017; Switch Transformer, 2022) replaces the FFN sublayer with a set of expert FFNs + a router. This means:

- **Attention stays dense**: The self-attention remains unchanged
- **FFN becomes sparse**: The feedforward layer is replaced by sparsely activated experts
- **Result**: The attention tensor still computes O(n²) but each token only activates a fraction of FFN parameters

### Alternative: MoE in Attention
Some works (reviewed in [[attention-moe-crossovers]]) replace attention heads with expert-style routing or make attention itself sparse.

## Why This Fusion is Important

The transformer's clean separation between "communication" (attention) and "computation" (FFN) creates a natural boundary for introducing sparsity:

- Attention handles cross-token mixing (can be made sparse via sparse attention)
- FFN handles per-token processing (can be made sparse via MoE)

This separation allows researchers to independently improve each sublayer, leading to the crossover works documented in [[attention-moe-crossovers]].
