---
title: "Attention Mechanism"
tags: [article, mechanism, deep-learning]
related: ["[[transformer-architecture]]", "[[cross-connections]]"]
created: 2026-05-18
updated: 2026-05-22
---

# Attention Mechanism

The attention mechanism allows neural networks to dynamically focus on different parts of the input when producing each output element. It was originally formalized for machine translation and later became the core of the Transformer architecture.

## Timeline

- **2016** — Bahdanau attention formalized for seq2seq models
- **2018** — The Transformer architecture was introduced, making attention the primary computation mechanism (replacing recurrence)
- **2020** — Attention emerges in GPT-3, scaling to 175B parameters

## Types of Attention

- **Bahdanau (additive) attention** — Uses a small feed-forward network to compute alignment scores
- **Luong (multiplicative) attention** — Computes alignment via dot product between encoder and decoder states
- **Self-attention (intra-attention)** — Attention within a single sequence, used in Transformers
- **Cross-attention** — Attention between different sequences (e.g., encoder-decoder)

## Scaled Dot-Product Attention

```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V
```

where Q, K, V are queries, keys, and values, and d_k is the key dimension.

## Connections

The [[transformer-architecture]] paper introduced multi-head self-attention. For a broader view of how attention relates to other mechanisms, see [[cross-connections]].
