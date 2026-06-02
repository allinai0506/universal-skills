---
title: "Mixture of Experts (MoE)"
tags: [concept, architecture, sparse-modeling]
sources: ["raw/articles/moe-2024.md"]
related: ["[[transformer-architecture]]", "[[sparse-moe-models]]"]
created: 2026-05-20
updated: 2026-05-25
---

# Mixture of Experts (MoE)

Mixture of Experts is a neural network architecture that uses multiple "expert" sub-networks with a learned router to activate only a subset of parameters for each input. This enables scaling model capacity without proportionally increasing compute.

## How It Works

1. **Experts** — Multiple independent feed-forward networks (typically 8-64)
2. **Router/Gate** — A learned linear layer that selects the top-k experts per token
3. **Sparse activation** — Only 1-2 experts active per token, enabling 3x-5x compute savings

## Key Developments

- **2024 MoE variants** — Achieve 3x sparse activation ratio improvements over dense baselines
- **Load balancing** — Auxiliary losses ensure uniform expert utilization
- **Expert parallelism** — Distribute experts across devices for trillion-scale models

## Models Using MoE

- Mixtral 8x7B (Mistral)
- GPT-4 (rumored MoE architecture)
- Switch Transformer (Google)

## Connections

- Built on [[transformer-architecture]] foundations
- [[sparse-moe-models]] represent the latest generation of efficient large-scale models

## Key Advantage

MoE achieves better quality per FLOP than dense transformers at large scales by routing each token to the most relevant experts, avoiding the cost of activating all parameters.
