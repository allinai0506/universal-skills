---
title: "Transformer Architecture Research Wiki"
tags: [index, transformer, moe]
created: 2026-06-02
updated: 2026-06-02
---

# Transformer Architecture Research Wiki

A curated knowledge base on transformer model architecture evolution, with a focus on Mixture of Experts (MoE) and sparse activation techniques.

## Articles

- [[Mixture of Experts 2024]] — Google's 2024 MoE breakthrough achieving 3x sparse activation ratio, plus a survey of key MoE innovations from 2022-2024

## Concepts

- [[Mixture of Experts]] — Architectural pattern where multiple specialized sub-networks (experts) are selectively activated per input token
- [[Sparse Activation]] — Technique where only a fraction of model parameters are active for any given input
- [[Expert Routing]] — Mechanisms for assigning tokens to experts (hard routing, soft routing, dynamic selection)
- [[Soft MoE]] — Google's 2023 approach replacing discrete token routing with soft weighted assignments

## Connections

- [[MoE Innovation Timeline]] — Chronological overview of MoE developments from Switch Transformer (2022) to Google's 2024 breakthrough

## Raw Sources

- `raw/articles/moe-2024.md` — "Mixture of Experts: Scaling Transformer Models Beyond Dense Limits"

## Related Topics

- Transformer architecture
- Model efficiency
- Sparse computation
- Large language model scaling
