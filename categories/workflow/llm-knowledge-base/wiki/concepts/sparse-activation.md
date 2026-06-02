---
title: "Sparse Activation"
tags: [sparsity, efficiency, computation]
related: [["Mixture of Experts"], ["Attention Mechanism"]]
created: 2026-06-02
updated: 2026-06-02
---

# Sparse Activation

Sparse activation refers to techniques where only a subset of model parameters or computational pathways are active for any given input.

## Two Main Paradigms

### Sparse Attention
Activates a subset of **token-to-token interactions** (receptive field sparsification):
- Window/local attention
- Global+sparse patterns
- Hash-based attention

### Sparse Experts (MoE)
Activates a subset of **expert sub-networks** (parameter sparsification):
- Top-k routing
- Conditional computation
- Expert selection

## The Sparsity Thesis

Many efficiency advances in large models can be understood as identifying and exploiting **sparsity**:

- **Data sparsity**: Not all tokens are equally important
- **Parameter sparsity**: Not all weights are needed for every input
- **Compute sparsity**: Not all operations are equally valuable

Attention and MoE attack sparsity from complementary angles — attention sparsifies the interaction space, MoE sparsifies the function space.
