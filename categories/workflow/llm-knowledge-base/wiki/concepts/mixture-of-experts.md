---
title: "Mixture of Experts"
tags: [moe, efficiency, sparsity, transformer]
related: [["Attention Mechanism"], ["Sparse Activation"], ["Soft Routing"]]
created: 2026-06-02
updated: 2026-06-02
---

# Mixture of Experts

Mixture of Experts (MoE) is a sparse gating architecture that scales model capacity without proportionally increasing compute. Instead of activating all parameters for every input, an MoE layer routes each token to a subset of expert sub-networks.

## Core Formulation

A standard MoE layer with $N$ experts $E_1, \ldots, E_N$ and a router $G$ computes:

$$y = \sum_{i=1}^N G(x)_i \cdot E_i(x)$$

Where $G(x)$ is typically a sparse gating function (e.g., top-k softmax).

## Key Innovations Timeline

| Year | Work | Contribution |
|------|------|--------------|
| 2017 | MoE in RNNs (Shazeer et al.) | First modern MoE with sparse gating and noisy top-k routing |
| 2022 | Switch Transformer (Google) | Simplified to top-1 routing; scaled to 2048 experts; 7x speedup |
| 2022 | DeepSpeed-MoE (Microsoft) | Hierarchical MoE, pyramid-shaped capacity, 3x speedup |
| 2022 | GLaM (Google) | Scaled MoE to 1.2T params with 64 experts; ~2x quality per FLOP |
| 2023 | Soft MoE (Google) | Replaced discrete routing with soft, attention-like assignment; eliminated load balancing loss |
| 2023 | Mixtral 8x7B (Mistral) | 46.7B total / 12.9B active params; matched Llama 2 70B at 6x speed |

## Routing Paradigms

1. **Hard routing (top-k)**: Each token is dispatched to exactly k experts. Simple but can cause load imbalance and expert collapse.
2. **Soft routing**: Each token is a weighted combination of all experts (Soft MoE). Improves gradient flow and eliminates expert collapse.
3. **Hash-based routing**: Fixed assignment via hash function (Hash Layers, Facebook 2022). No learned router, no load balancing issues.

## MoE in Transformers

The dominant integration point is replacing the feed-forward network (FFN) in each Transformer block with an MoE layer. The self-attention sub-layer remains unchanged. This means:

- **Attention** handles inter-token communication (dense, O(n²))
- **MoE** handles per-token computation (sparse, O(n) in expert count)
- This divide mirrors the "communication vs. computation" separation

## Open Challenges

- **Expert collapse**: Some experts may stop being selected (dying neuron problem)
- **Load imbalance**: Non-uniform token distribution across experts
- **Fine-tuning difficulty**: MoE models are harder to adapt than dense models
- **Memory overhead**: All expert weights must be loaded in memory
- **Batch size constraints**: Smaller batches can underutilize expert capacity

## Connections

- Shares the **routing paradigm** with [[attention-mechanism]] — both use input-dependent routing with softmax-based weight assignment
- Multi-expert architectures are conceptually parallel to multi-head attention
- [[soft-routing]] bridges the discrete-continuous divide between hard MoE and attention
