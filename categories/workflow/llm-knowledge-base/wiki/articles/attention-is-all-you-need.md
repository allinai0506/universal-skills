---
title: "Attention Is All You Need: The Transformer Architecture"
tags: [attention, transformer, foundation]
sources: ["Vaswani et al., 2017"]
related: [["Attention Mechanism"], ["Mixture of Experts"], ["MoE Architecture Overview"]]
created: 2026-06-02
updated: 2026-06-02
---

# Attention Is All You Need

The Transformer architecture (Vaswani et al., 2017) replaced recurrence with attention, establishing the architectural template that dominates modern NLP and beyond.

## Architectural Summary

A Transformer block consists of two sub-layers:
1. **Multi-Head Self-Attention**: Content-based routing between tokens
2. **Feed-Forward Network (FFN)**: Independent per-token computation

This separation of **communication** (attention) and **computation** (FFN) is the key architectural insight that also enables MoE integration — the FFN sub-layer is a natural drop-in replacement for an MoE layer.

## Why the FFN is Replaceable

The FFN in a Transformer is position-wise and independent per token. MoE works by replacing the single FFN with multiple expert FFNs. This preserves the architectural structure while introducing sparsity.

## From Attention to MoE

The step from Transformer to MoE-Transformer is straightforward:

```
Standard Transformer Block:
  x → Self-Attention → FFN(x) → x'

MoE Transformer Block:
  x → Self-Attention → Σ G(x)_i · Expert_i(x) → x'
```

Where attention handles the inter-token routing and the MoE layer handles per-token computation scaling.
