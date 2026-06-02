---
title: "Transformer Architecture"
tags: [transformer, architecture, attention, foundation]
sources: ["evals/fixtures/raw/articles/moe-2024.md"]
related: ["[[Attention Mechanism]]", "[[MoE Evolution]]", "[[Post-MoE Trends]]"]
created: 2026-06-02
updated: 2026-06-02
---

# Transformer Architecture

The Transformer architecture, introduced by Vaswani et al. in the 2017 paper "Attention Is All You Need," is the foundational architecture behind virtually all modern Large Language Models (LLMs).

## Architecture Overview

The original Transformer consists of:

- **Encoder-Decoder structure**: An encoder processes the input sequence, while a decoder generates output
- **Self-attention layers**: Allow each token to attend to all other tokens in the sequence
- **Feed-forward networks (FFN)**: Process each token independently after attention
- **Positional encoding**: Injects sequence position information since attention is permutation-invariant
- **Layer normalization & residual connections**: Stabilize training of deep networks

## Key Innovation: Self-Attention

The self-attention mechanism computes a weighted sum of values based on the similarity between queries and keys:

```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
```

This allows the model to capture long-range dependencies without the sequential bottleneck of RNNs.

## Scaling Properties

Transformers scale remarkably well with:
- **More parameters** → better performance (scaling laws by Kaplan et al., 2020)
- **More data** → continued improvement (Chinchilla scaling laws, Hoffmann et al., 2022)
- **More compute** → predictable capability gains

## Limitations

- **Quadratic attention cost**: O(n²) in sequence length, limiting long-context processing
- **Dense computation**: Every parameter activates for every token, leading to high inference cost
- **KV cache pressure**: Large memory footprint for autoregressive generation

## Legacy

The Transformer has become the universal backbone for NLP, computer vision (ViT), speech (Whisper), and multimodal models. Its dominance is now being challenged by newer architectures that address its fundamental limitations, particularly around quadratic attention and dense computation.

Related: [[Attention Mechanism]], [[MoE Evolution]]
