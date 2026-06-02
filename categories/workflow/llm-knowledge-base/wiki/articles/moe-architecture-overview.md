---
title: "MoE Architecture Overview: From Static Ensembles to Dynamic Sparse Systems"
tags: [moe, transformer, efficiency, sparsity]
sources: ["raw/articles/moe-2024.md"]
related: [["Attention Mechanism"], ["Mixture of Experts"]]
created: 2026-06-02
updated: 2026-06-02
---

# MoE Architecture Overview

Mixture of Experts (MoE) has evolved from static ensemble methods into a cornerstone technique for scaling modern Transformer-based language models. This article synthesizes findings from the 2024 MoE survey and contextualizes them within the broader architecture landscape.

## The MoE + Transformer Marriage

The most impactful architectural decision in recent MoE research is the integration of MoE layers **inside** Transformer blocks. Specifically, the feed-forward network (FFN) sub-layer is replaced with an MoE layer comprising multiple smaller FFNs (experts), while the self-attention sub-layer remains unchanged.

This creates a clean architectural separation:

| Sub-layer | Role | Computation |
|-----------|------|-------------|
| Self-Attention | Inter-token routing (communication) | Dense, O(n²) |
| MoE-FFN | Per-token computation | Sparse, O(n * k) |

## Sparse Activation Breakthrough (2024)

The most recent work (Google, 2024) achieves a 3x improvement in sparse activation ratio — only ~10% of parameters activate per token versus the previous ~30-35%. Key techniques:

1. **Dynamic expert selection**: Compatibility scores between tokens and expert representations replace learned gating
2. **Expert specialization pressure**: An auxiliary loss promoting distinct expert specializations without explicit capacity constraints
3. **Staged training**: Dense pre-training followed by progressive sparsification

## The Three Routing Generations

MoE routing has undergone three distinct phases, each borrowing from and diverging from attention mechanisms:

1. **Hard top-k routing** (Switch Transformer, Mixtral): Discrete selection of k experts. Simple but prone to load imbalance and requires auxiliary losses.
2. **Soft routing** (Soft MoE): Continuous assignment where each token is a weighted combination of all experts. Eliminates collapse and load balancing losses.
3. **Attention-based routing** (emerging): Using attention-like mechanisms to compute expert affinities, blurring the line between attention and expert selection.
