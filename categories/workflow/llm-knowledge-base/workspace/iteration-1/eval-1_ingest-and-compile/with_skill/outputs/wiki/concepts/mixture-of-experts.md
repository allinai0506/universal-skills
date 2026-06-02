---
title: "Mixture of Experts"
tags: [concept, architecture, moe, efficiency]
sources: ["raw/articles/moe-2024.md"]
related: ["[[Sparse Activation]]", "[[Expert Routing]]", "[[Soft MoE]]", "[[Mixture of Experts 2024]]", "[[MoE Innovation Timeline]]"]
created: 2026-06-02
updated: 2026-06-02
---

# Mixture of Experts

## Definition

Mixture of Experts (MoE) is an architectural pattern for neural networks where multiple specialized sub-networks ("experts") are selectively activated per input token. A router/gating network determines which experts to use for each input, enabling the model to have a large total parameter count while keeping per-token computation low.

## Key Characteristics

- **Sparse activation**: Only a fraction of experts activate per token, reducing FLOPs per inference
- **Expert specialization**: Each expert learns to handle different types of inputs or subtasks
- **Router/gating mechanism**: A learned component that selects which experts to activate
- **Total vs. active parameters**: MoE models are described by both (e.g., Mixtral 8x7B has 46.7B total, 12.9B active)

## Variants

| Variant | Routing Type | Key Innovation |
|---------|-------------|----------------|
| Switch Transformer | Top-1 hard routing | Simplest routing; scales to 2048 experts |
| DeepSpeed-MoE | Hierarchical | Pyramid-shaped expert allocation |
| Soft MoE | Soft/weighted routing | Eliminates load balancing loss |
| Mixtral 8x7B | Top-2 hard routing | Production-scale deployment |
| Google 2024 | Dynamic selection | ~10% activation ratio |

## Tradeoffs

- **Advantages**: Higher model capacity at similar inference cost; better quality-per-FLOP
- **Disadvantages**: Harder to fine-tune; complex serving infrastructure; risk of expert collapse; load balancing challenges

## Connections

- Enables [[Sparse Activation]] at scale — the two concepts are deeply linked
- [[Expert Routing]] is the core mechanism that makes MoE work
- [[Soft MoE]] represents a fundamentally different approach to the routing problem
- [[Mixture of Experts 2024]] covers the latest breakthroughs
