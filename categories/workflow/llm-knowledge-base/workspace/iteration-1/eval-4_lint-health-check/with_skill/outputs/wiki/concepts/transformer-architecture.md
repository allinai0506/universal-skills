---
title: "Transformer Architecture"
tags: [concept, architecture, deep-learning]
sources: ["raw/articles/moe-2024.md"]
related: ["[[attention-mechanism]]", "[[mixture-of-experts]]"]
created: 2026-05-15
updated: 2026-05-20
---

# Transformer Architecture

The Transformer architecture was introduced in **2017** by Vaswani et al. in the paper "Attention Is All You Need." It replaced recurrent neural networks as the dominant architecture for sequence modeling.

## Key Innovations

- **Self-attention mechanism** — Allows each token to attend to every other token in the sequence
- **Multi-head attention** — Multiple attention heads capture different relationship types
- **Positional encoding** — Sine/cosine functions to encode position information
- **Layer normalization and residual connections** — Enable deep (12+ layer) training stability

## Scaling

Early transformers had 65M-213M parameters (BERT-base, BERT-large). Modern variants reach hundreds of billions of parameters through techniques like mixture of experts, model parallelism, and quantization techniques from 2023.

## Impact

Transformers unlocked large language models (GPT series), multimodal models, and have been applied beyond NLP to vision (ViT), audio (Whisper), and protein folding (AlphaFold).

## Connections

- The [[attention-mechanism]] is the core component
- [[mixture-of-experts]] extends the transformer by adding sparse feed-forward layers
- Quantization enables efficient deployment of large transformer models on consumer hardware
