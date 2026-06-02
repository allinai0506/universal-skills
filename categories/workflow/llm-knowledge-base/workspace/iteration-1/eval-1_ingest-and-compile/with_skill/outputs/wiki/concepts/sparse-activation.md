---
title: "Sparse Activation"
tags: [concept, efficiency, sparsity, computation]
sources: ["raw/articles/moe-2024.md"]
related: ["[[Mixture of Experts]]", "[[Expert Routing]]"]
created: 2026-06-02
updated: 2026-06-02
---

# Sparse Activation

## Definition

Sparse activation is a technique where only a fraction of a model's parameters are active (computed) for any given input token. This contrasts with dense models where all parameters participate in every forward pass.

## Key Metrics

- **Sparse activation ratio**: The fraction of total parameters that remain inactive per token. Higher is better for efficiency.
- **Active parameters per token**: The number of parameters actually computed. Determines inference cost.
- **Total parameter count**: The full model size, including inactive experts. Determines memory requirements.

## Historical Progression

| Era | Typical Active Parameters | Typical Sparse Activation Ratio |
|-----|--------------------------|--------------------------------|
| Pre-MoE (dense) | 100% | 0% |
| Switch Transformer (2022) | ~35% | ~65% |
| Mixtral 8x7B (2023) | ~28% | ~72% |
| Google 2024 | ~10% | ~90% |

## Techniques for Increasing Sparsity

1. **Dynamic expert selection**: Compute compatibility scores between tokens and expert representations rather than using a learned router
2. **Expert specialization pressure**: Auxiliary loss that encourages distinct expert specializations without explicit capacity constraints
3. **Staged training**: Train in dense mode first, then progressively increase sparsity

## Connections

- Sparse activation is the primary benefit of [[Mixture of Experts]] architectures
- [[Expert Routing]] mechanisms determine which parameters activate
- The 3x improvement in sparse activation ratio (from ~30% to ~10%) is the headline result of [[Mixture of Experts 2024]]
