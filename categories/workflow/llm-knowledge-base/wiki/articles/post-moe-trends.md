---
title: "Post-MoE Trends in LLM Architecture"
tags: [architecture, state-space-models, linear-attention, hybrid, mamba]
sources: []
related: ["[[Transformer Architecture]]", "[[MoE Evolution]]", "[[Sparse Activation]]"]
created: 2026-06-02
updated: 2026-06-02
---

# Post-MoE Trends: Beyond the Transformer

While MoE optimizes Transformers by adding sparsity, a new wave of architectures questions the Transformer foundation entirely.

## State Space Models (SSMs)

### Mamba (Gu & Dao, 2023-2024)
The most prominent SSM alternative to Transformers:

- **Linear-time inference** (O(n) instead of O(n²))
- **Selection mechanism**: Allows the model to selectively focus on relevant input
- **Hardware-aware implementation**: Uses parallel scan for efficient training
- **Matches Transformer quality** on language tasks at comparable sizes
- **Unlimited context length** in theory — no KV cache bottleneck

Key insight: SSMs are recurrence-based (like RNNs) but can be trained efficiently in parallel (like Transformers).

### Mamba-2 (2024)
- Unified SSM and attention mechanisms in a single theoretical framework
- State space duality: shows SSMs and attention are mathematically connected
- 2-8x faster than Mamba-1 on long sequences

## Linear Attention / Efficient Attention

### RWKV (2023-2024)
A hybrid architecture that combines Transformer-style training with RNN-style inference:

- **Linear attention** via time-dependent recurrent formulation
- **Token-shift mechanism**: Captures positional information without explicit positional encoding
- **5-10x faster inference** than equivalent Transformer
- **CPU-friendly**: Can run large models on consumer hardware

### RetNet (Microsoft, 2023)
- Retention mechanism as replacement for attention
- Training parallelism of Transformers + inference efficiency of RNNs
- **Low-cost inference** with O(1) memory per layer

## Hybrid Approaches (2024-2025)

The emerging consensus is that **hybrid architectures** combining multiple mechanisms work best:

- **Jamba (AI21 Labs, 2024)**: Combines Mamba SSM layers with Transformer attention layers and MoE FFN layers — a "hybrid of hybrids"
- **Samba (Microsoft, 2024)**: Interleaves Mamba and attention layers
- **StripedHyena (Together, 2023)**: Uses attention + gated convolutions

## Industry Trends (2025-2026)

1. **Massive MoE deployment**: GPT-4, Gemini, and other frontier models all use MoE at scale
2. **Long context arms race**: 1M+ token contexts (Gemini 1.5 Pro, Claude 3.5)
3. **Architecture convergence**: Attention + SSM hybrids becoming the new default
4. **Hardware co-design**: Architectures co-optimized with inference hardware
5. **Distilled specialized models**: Smaller dense models distilled from large MoE teachers

## Key Takeaway

The field is moving from "one architecture dominates all" (pure Transformer, 2017-2023) toward **specialized hybrid designs** where different mechanisms handle different aspects of the problem — attention for recall, SSMs for efficiency, MoE for capacity.

Related: [[Transformer Architecture]], [[MoE Evolution]], [[Sparse Activation]]
