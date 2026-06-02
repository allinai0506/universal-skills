---
title: "MoE Evolution"
tags: [moe, sparsity, efficiency, scaling, mixture-of-experts]
sources: ["evals/fixtures/raw/articles/moe-2024.md"]
related: ["[[Transformer Architecture]]", "[[Sparse Activation]]", "[[Post-MoE Trends]]"]
created: 2026-06-02
updated: 2026-06-02
---

# MoE Evolution: Mixture of Experts

Mixture of Experts (MoE) is a sparse architecture that scales Transformer models beyond dense limits by activating only a subset of parameters per token.

## Core Idea

Instead of one large FFN layer, MoE replaces it with multiple "expert" FFNs and a router that selects which experts to use for each token. This achieves:

- **Total parameters >> active parameters** (e.g., 46.7B total, 12.9B active for Mixtral 8x7B)
- **Much lower inference cost** at comparable quality to dense models
- **Better specialization** — each expert develops expertise on different token types

## Timeline of Key Innovations

### 2022: Switch Transformer (Google)
- Simplified MoE routing to **top-1 expert selection** ("hard routing")
- Showed that increasing expert count (up to 2048) continues to improve efficiency
- Achieved **7x increase in pretraining speed** over dense baselines

### 2022: DeepSpeed-MoE (Microsoft)
- Introduced **hierarchical MoE** with multiple expert groups
- Pyramid-shaped expert capacity allocation
- Achieved **3x speedup** over dense models at comparable quality

### 2023: Soft MoE (Google)
- Replaced discrete token routing with **soft assignment**
- Eliminated the load balancing loss entirely
- Each token is a weighted combination of all experts
- Better gradient flow and training stability

### 2023: Mixtral 8x7B (Mistral)
- **46.7B total parameters, 12.9B active** per token
- Matched or exceeded Llama 2 70B and GPT-3.5 on most benchmarks
- **6x faster inference** than comparable dense models
- Demonstrated that MoE can be commercially viable

### 2024: 3x Sparse Activation Ratio (Google)
- Only **~10% of parameters activate** per token (vs. previous ~30-35%)
- Key techniques:
  - Dynamic expert selection via compatibility scoring
  - Expert specialization pressure through auxiliary loss
  - Staged training: dense → progressive sparsity

## Open Challenges

- **Load balancing** across experts remains tricky at extreme scales
- **Expert collapse** — some experts can become unused (specialization fragility)
- **Fine-tuning difficulty** — MoE models prone to catastrophic forgetting
- **Infrastructure complexity** — all expert weights must be kept in memory
- **Communication overhead** — expert parallelism requires significant all-to-all communication

Related: [[Sparse Activation]], [[Transformer Architecture]], [[Post-MoE Trends]]
