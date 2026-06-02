---
title: "Attention Mechanism"
tags: [attention, transformer, sequence-modeling]
related: [["Mixture of Experts"], ["Multi-Head Attention"]]
created: 2026-06-02
updated: 2026-06-02
---

# Attention Mechanism

The attention mechanism is the foundational operation behind the Transformer architecture (Vaswani et al., 2017), enabling models to dynamically weigh the importance of different tokens in a sequence when computing representations.

## Scaled Dot-Product Attention

At its core, attention computes a weighted sum of values, where the weights are derived from a compatibility function between queries and keys:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) V$$

This operation is **content-based routing**: each token "attends to" all other tokens proportionally to how relevant they are.

## Key Properties

1. **Dynamic computation graph**: The attention matrix is input-dependent, not statically determined.
2. **Global receptive field**: Every token can directly interact with every other token (unlike RNNs or CNNs).
3. **Content-based routing**: The softmax over keys acts as a routing mechanism — tokens are routed to other tokens based on learned compatibility.

## Multi-Head Attention

Transformers use multiple parallel attention heads, each potentially learning different relationship types:

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O$$

This is conceptually parallel to having multiple "expert" attention mechanisms that the model can draw from — a motif that recurs in Mixture of Experts.

## Sparse Attention Variants

Several works aim to reduce the quadratic cost of full attention:

- **Local/Windowed attention** — restrict to nearby tokens
- **Global + local** — sparse patterns with designated global tokens (Longformer, BigBird)
- **Hash-based attention** (Reformer) — LSH-based bucketing
- **Latent attention** (Performer) — kernel-based approximation

## Attention is Routing

A critical insight: **attention is a routing mechanism**. The softmax computes a probability distribution over destinations (key positions), and the output is a weighted combination of values at those destinations. This is structurally analogous to how an MoE router computes a probability distribution over experts and returns a weighted combination of expert outputs.

## Connections

- Related to [[mixture-of-experts]] via shared routing paradigm
- Multi-head parallelism mirrors multi-expert design
- Soft MoE replaces discrete expert routing with attention-like assignment
