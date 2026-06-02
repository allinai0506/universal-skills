---
title: "MoE Innovation Timeline"
tags: [connection, timeline, moe, evolution]
sources: ["raw/articles/moe-2024.md"]
related: ["[[Mixture of Experts]]", "[[Mixture of Experts 2024]]", "[[Expert Routing]]", "[[Sparse Activation]]", "[[Soft MoE]]"]
created: 2026-06-02
updated: 2026-06-02
---

# MoE Innovation Timeline

A chronological overview of key MoE developments in transformer models from 2022 to 2024.

## Timeline

### 2022: Foundation Work

**Switch Transformer (Google)**
- Simplified routing to top-1 expert selection
- Demonstrated scaling to 2048 experts
- Achieved 7x pretraining speedup
- Established that more experts = better efficiency even with simple routing

**DeepSpeed-MoE (Microsoft)**
- Introduced hierarchical MoE with multiple expert groups
- Pyramid-shaped expert capacity allocation
- 3x speedup over dense models at comparable quality
- Focused on practical training infrastructure

### 2023: Production and Alternatives

**Soft MoE (Google)**
- Paradigm shift: soft assignment instead of discrete routing
- Eliminated load balancing loss
- Better gradient flow
- All experts contribute to every token

**Mixtral 8x7B (Mistral)**
- First production-scale open MoE model
- 46.7B total parameters / 12.9B active
- Matched/exceeded Llama 2 70B and GPT-3.5
- 6x faster inference than comparable dense models
- Proved MoE viability in real-world deployments

### 2024: The Next Leap

**Google's 3x Sparse Activation Breakthrough**
- Reduced active parameters from ~30-35% to ~10% per token
- Three key techniques:
  1. Dynamic expert selection (compatibility scoring instead of learned router)
  2. Expert specialization pressure (auxiliary loss for distinct specializations)
  3. Staged training (dense first, then progressive sparsification)

## Research Trajectory

The evolution shows a clear trend:
1. **Simplicity**: Switch Transformer proved simple routing works at scale
2. **Diversity**: Soft MoE and Mixtral explored different routing philosophies
3. **Efficiency**: The 2024 breakthrough pushed sparsity to its practical limit

## Open Questions

- Can sparse activation ratios go below 10%?
- Can dynamic selection be combined with soft routing ideas?
- Will production infrastructure catch up to support extreme MoE at scale?
- Can MoE fine-tuning challenges be solved (or is post-training adaptation fundamentally harder)?

## Connections

- All developments are variants of [[Mixture of Experts]] architecture
- [[Expert Routing]] is the dimension along which most innovation occurred
- [[Sparse Activation]] ratio improved from ~35% to ~10% over this period
- [[Soft MoE]] represents the most radical departure from traditional routing
