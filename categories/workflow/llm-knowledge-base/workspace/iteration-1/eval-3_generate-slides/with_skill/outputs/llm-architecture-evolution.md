---
marp: true
theme: default
class: default
paginate: true
---

# LLM Architecture Evolution
## Transformer -> MoE -> Beyond

**Source:** ML Architecture Research Wiki

---

# 1. The Transformer (2017) — The Foundation

Introduced by Vaswani et al. in "Attention Is All You Need"

- **Self-attention**: `Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) V`
- Encoder-decoder structure with parallelized training
- First architecture to **eliminate recurrence** while capturing long-range dependencies

**Why it won:** Unprecedented scaling behavior — more parameters, data, and compute all predictably improve performance.

> Source: [[transformer-architecture]]

---

# 2. Transformer Limitations

The dense transformer has fundamental scaling bottlenecks:

| Problem | Impact |
|---------|--------|
| **Quadratic attention** | O(n^2) in sequence length — limits long context |
| **Dense FFN** | Every parameter activates for every token — high compute at inference |
| **KV cache pressure** | Memory footprint grows with sequence length |

The field split into two tracks:
- **MoE** — make FFN sparse (more params, same compute)
- **SSMs** — make attention linear (long context, efficient inference)

> Source: [[transformer-architecture]], [[post-moe-trends]]

---

# 3. Mixture of Experts — Sparse Scaling

Instead of one large FFN, MoE uses **multiple expert FFNs** with a router:

```
Token ──> Router ──> Expert A ──┐
                 └─> Expert B ──┤──> Output
                 └─> Expert C ──┘
```

**Key numbers:**
- Mixtral 8x7B: **46.7B total / 12.9B active** params
- Switch Transformer: **7x pretraining speedup** over dense baseline
- **~30-35% of params active** per token (2 experts in top-2 routing)

> Source: [[moe-evolution]]

---

# 4. MoE Timeline — Key Milestones

| Year | Innovation | Impact |
|------|-----------|--------|
| **2022** | Switch Transformer (Google) | Top-1 routing, 2048 experts, 7x speedup |
| **2022** | DeepSpeed-MoE (Microsoft) | Hierarchical MoE, pyramid allocation, 3x speedup |
| **2023** | Soft MoE (Google) | Soft routing — no load balancing loss, better gradient flow |
| **2023** | Mixtral 8x7B (Mistral) | Commercial viability — beats Llama 2 70B at 6x faster inference |
| **2024** | 3x Sparse Activation (Google) | Only **~10% params active** per token |

**Open challenges:** Load balancing, expert collapse, fine-tuning difficulty, infrastructure complexity.

> Source: [[moe-evolution]]

---

# 5. Beyond the Transformer — State Space Models

**Mamba** (Gu & Dao, 2023-2024): The most prominent SSM alternative

- **Linear-time inference**: O(n) instead of O(n^2)
- **Selection mechanism**: Dynamic focus on relevant input
- **Matches Transformer quality** at comparable sizes
- **Unlimited context length** in theory

**Mamba-2 (2024):** Unified SSM and attention — showed the **state space duality theorem**, proving SSMs and attention are mathematically related.

> Source: [[post-moe-trends]]

---

# 6. Linear Attention & Hybrid Architectures

| Architecture | Approach | Key Advantage |
|-------------|----------|---------------|
| **RWKV** | Linear attention + RNN-style inference | 5-10x faster inference, CPU-friendly |
| **RetNet** | Retention mechanism | O(1) memory per layer |
| **Jamba** | Mamba + Attention + MoE | "Hybrid of hybrids" |
| **Samba** | Interleaved Mamba + Attention | Best of both worlds |
| **StripedHyena** | Attention + gated convolutions | Alternative mix |

The **emerging consensus**: Hybrid architectures combining attention + SSM + MoE outperform any single approach.

> Source: [[post-moe-trends]]

---

# 7. Industry Landscape (2025-2026)

**Massive MoE deployment:**
- GPT-4, Gemini, and all frontier models use MoE at scale
- Distilled specialized models trained from large MoE teachers

**Long context arms race:**
- 1M+ token contexts (Gemini 1.5 Pro, Claude)

**Hardware co-design:**
- Architectures co-optimized with inference silicon

**The trajectory:**
```
Pure Transformer (2017) ──> MoE Transformers (2022-2024) ──> Hybrid SSM+Attn+MoE (2025+)
```

> Source: [[post-moe-trends]]

---

# 8. Key Takeaways

1. **No single architecture wins everything** — specialization is the trend
2. **MoE is table stakes** — all frontier models use sparsity for capacity
3. **SSMs fix the context bottleneck** — linear attention enables unlimited context
4. **Hybrids are the future** — attention for recall, SSMs for efficiency, MoE for scale
5. **Hardware co-design** — architecture and silicon evolve together

> Full wiki: `wiki/index.md` | Articles: [[transformer-architecture]], [[moe-evolution]], [[post-moe-trends]]
