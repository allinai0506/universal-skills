---
title: "ML Architecture Research Wiki"
created: 2026-06-02
updated: 2026-06-02
---

# ML Architecture Research Wiki

A structured knowledge base chronicling the evolution of deep learning architectures, from the Transformer revolution to modern sparse and mixture-of-experts models.

## Table of Contents

### Concepts

- [[attention-mechanism]] — Core mechanism enabling dynamic token-to-token interaction in sequence models
- [[mixture-of-experts]] — Sparse gating paradigm that scales model capacity without proportional compute cost
- [[sparse-activation]] — Techniques for activating only a subset of parameters per input
- [[soft-routing]] — Continuous, differentiable alternatives to hard discrete routing
- [[soft-moe]] — The most direct architectural bridge between attention and MoE
- [[transformer-architecture]] — The Transformer as a fusion point for attention and MoE
- [[transformer-evolution]] — How Transformer architecture has evolved from 2017 to present
- [[expert-routing]] — Routing strategies for MoE models
- [[scaling-laws]] — Empirical relationships between model size, data, and compute
- [[top-k-routing]] — Standard hard routing for MoE (Switch Transformer, Mixtral)
- [[deep-routing]] — Emerging end-to-end learned routing policies
- [[moe-scaling-properties]] — How scaling laws differ for sparse MoE models
- [[expert-collapse]] — Failure mode where experts stop being selected
- [[load-balancing]] — Ensuring tokens are evenly distributed across experts
- [[neural-routing]] — The broader routing paradigm unifying attention and MoE
- [[conditional-computation]] — Compute-on-demand paradigm
- [[feedforward-networks]] — The FFN layer that MoE replaces
- [[multi-head-attention]] — Multi-head attention as a multi-expert analog

### Articles

- [[transformer-architecture|Transformer Architecture]] — The foundation of modern LLMs
- [[mixture-of-experts-scaling-transformers|Mixture of Experts: Scaling Beyond Dense Limits]] — MoE innovations 2022-2024
- [[moe-evolution|MoE Evolution]] — Detailed timeline and breakthroughs
- [[post-moe-trends|Post-MoE Trends]] — SSMs, linear attention, and hybrid architectures
- [[attention-is-all-you-need]] — The original Transformer paper
- [[moe-architecture-overview]] — From static ensembles to dynamic sparse systems
- [[moe-2024-breakthroughs]] — 2024's 3x sparse activation ratio breakthrough

### Connections

- [[connections|Cross-Concept Connections]] — Relationships between key concepts
- [[llm-architecture-connections|LLM Architecture Evolution Connections]] — Detailed architecture connections
- [[attention-moe-crossover]] — Documented crossovers between attention and MoE
- [[gaps-and-supplements]] — Gaps and supplements identified during query workflow

## Tag Index

- `#transformer` — Transformer architecture and variants
- `#moe` — Mixture of Experts
- `#attention` — Attention mechanisms
- `#efficiency` — Compute and memory efficiency
- `#sparsity` — Sparse computation
- `#routing` — Token-to-expert or token-to-token routing
- `#ssm` — State Space Models
- `#hybrid` — Hybrid architectures

## Source Articles

| Source | Article | Type |
|--------|---------|------|
| raw/articles/moe-2024.md | [[mixture-of-experts-scaling-transformers\|MoE Survey]] | Survey |
