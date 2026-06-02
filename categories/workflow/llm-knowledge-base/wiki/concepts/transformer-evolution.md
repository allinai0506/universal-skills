---
title: "Transformer Evolution"
tags: [transformer, architecture-evolution, scaling]
sources: ["wiki/articles/transformer-architecture.md", "wiki/articles/moe-evolution.md", "wiki/articles/post-moe-trends.md"]
related: ["[[Transformer Architecture]]", "[[MoE Evolution]]", "[[Post-MoE Trends]]"]
created: 2026-06-02
updated: 2026-06-02
---

# Transformer Evolution

The Transformer architecture has undergone a remarkable evolution from a single design to a diverse family of architectures.

## The Evolution Path

```
2017: Original Transformer (Vaswani et al.)
  └─► 2018: GPT / BERT (decoder-only / encoder-only divergence)
       └─► 2020: GPT-3 (scaling laws era begins)
            └─► 2022: Switch Transformer / PaLM (first major MoE)
                 └─► 2023: LLaMA, GPT-4 (dense refinements + MoE at scale)
                      └─► 2023-24: Mixtral, Mamba, RWKV (divergence: MoE + alternatives)
                           └─► 2025-26: Hybrid architectures (attention + SSM + MoE)
```

## Key Lessons

1. **Dense scaling hit diminishing returns** → MoE became essential for cost-effective scaling
2. **Quadratic attention is the next bottleneck** → SSMs and linear attention emerged
3. **The best architecture depends on deployment** — dense for small models, MoE for large, SSMs for long-context
4. **Convergence is happening** — modern designs pick the best mechanism for each subproblem

Related: [[Transformer Architecture]], [[MoE Evolution]], [[Post-MoE Trends]], [[Attention Mechanism]]
