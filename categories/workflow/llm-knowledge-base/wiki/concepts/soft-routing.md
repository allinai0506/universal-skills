---
title: "Soft Routing"
tags: [routing, attention, moe]
related: [["Attention Mechanism"], ["Mixture of Experts"]]
created: 2026-06-02
updated: 2026-06-02
---

# Soft Routing

Soft routing is the paradigm of continuous, differentiable assignment of inputs to computational pathways — as opposed to discrete (hard) routing that selects a single pathway.

## Key Examples

1. **Attention is soft routing**: The softmax over keys produces a probability distribution, and the output is a weighted combination over **all** positions. There is no hard selection of "which token to attend to."

2. **Soft MoE routing**: Instead of dispatching each token to exactly k experts, Soft MoE computes a weighted combination over all experts. Each token influences all experts' outputs proportionally.

3. **Mixture of Softmaxes**: A method for improving Softmax output distributions by combining multiple softmax "experts."

## Why Soft Routing Matters

Soft routing provides better gradient flow because the routing decision itself is differentiable. Hard top-k routing requires workarounds like straight-through estimators or auxiliary load-balancing losses.

## Connections

- [[attention-mechanism]] is the canonical example of soft routing
- [[mixture-of-experts]] has both hard (Switch Transformer, Mixtral) and soft (Soft MoE) variants
- The convergence of attention-inspired soft routing with MoE is an active research direction
