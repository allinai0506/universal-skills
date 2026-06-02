---
marp: true
theme: uncover
class:
  - lead
  - invert
paginate: true
---

# <!-- fit --> LLM Architecture Evolution

**From Transformer to MoE to Beyond**

A journey through the architectures powering modern AI

2026-06-02 | Knowledge Base Compilation

---

<!-- _class: default -->

# The Transformer Foundation (2017)

**"Attention Is All You Need" — Vaswani et al.**

```
Input → [Self-Attention → Add & Norm → FFN → Add & Norm] × N → Output
```

### Key innovations:
- **Self-attention**: Every token attends to every other token
- **Multi-head attention**: Parallel attention for different relationship types
- **Positional encoding**: Sequence order without recurrence
- **Residual connections + LayerNorm**: Stable deep network training

> The Transformer became the universal backbone for NLP, vision, speech, and multimodal AI.

---

# Attention: The Core Mechanism

**Scaled Dot-Product Attention**

$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) V
$$

### Why attention matters:
- **Content-based routing**: Each token finds relevant tokens dynamically
- **Global receptive field**: No distance penalty (unlike RNNs/CNNs)
- **Parallelizable**: Full sequence processed in one forward pass

### The cost: **O(n²)** compute — every token attends to every token

> Attention is also a **routing mechanism** — softmax routes tokens to relevant sources, structurally analogous to MoE routing.

---

# Scaling Laws & the Dense Limit

### The scaling era (2020-2022)

| Law | Finding |
|-----|---------|
| **Kaplan et al. (2020)** | Bigger models → better performance (power law) |
| **Chinchilla (2022)** | Model size & data must scale proportionally |

### The problem: **Dense computation hits a wall**

- GPT-3: 175B parameters, **all active** per token
- Inference cost grows linearly with parameter count
- Doubling parameters = 2x compute = 2x cost

**Insight:** Most parameters are wasted on any single input — a "math expert" shouldn't activate for "the cat sat on the mat."

---

# Mixture of Experts: Sparse Activation

**The solution: activate only what you need**

```
Standard FFN:      y = FFN(x)           — all params active
MoE FFN:           y = Σ G(x)_i · E_i(x) — only top-k experts
```

### Key innovation:
- Replace FFN with **multiple expert FFNs** + a **router**
- Each token activates only **k experts** (e.g., 2 of 8)

### Real-world impact (Mixtral 8x7B, 2023):

| Metric | Dense (70B) | MoE (46.7B) |
|--------|-------------|-------------|
| Active params | 70B | **12.9B** |
| Quality | Baseline | **Matches/exceeds** |
| Inference speed | 1x | **6x faster** |

---

# MoE Innovation Timeline

**From research to production (2022-2024)**

| Year | Work | Breakthrough |
|------|------|-------------|
| 2022 | **Switch Transformer** (Google) | Top-1 routing; scaled to **2048 experts**; 7x pretraining speedup |
| 2022 | **DeepSpeed-MoE** (Microsoft) | Hierarchical MoE; pyramid-shaped capacity; **3x speedup** |
| 2022 | **GLaM** (Google) | **1.2T params**, 64 experts; ~2x quality per FLOP |
| 2023 | **Soft MoE** (Google) | Replaced discrete routing with **soft attention-like assignment** |
| 2023 | **Mixtral 8x7B** (Mistral) | **Production-ready**: 46.7B total / 12.9B active; matches Llama 2 70B |
| 2024 | **3x sparsity** (Google) | Only **~10%** params active per token via dynamic selection |

### Open challenges:
- Expert collapse, load balancing, fine-tuning difficulty, infrastructure complexity

---

# Beyond Transformers: SSMs & Linear Attention

**The next frontier — questioning the Transformer foundation itself**

### State Space Models (Mamba, 2023-2024)
- **Linear O(n)** inference vs. Transformer's **O(n²)**
- **Selection mechanism**: model decides what to remember
- **Unlimited context** — no KV cache bottleneck
- **Mamba-2** (2024): Unified SSM + attention theory

### Linear Attention (RWKV, RetNet)
- **RWKV**: Transformer-quality training + RNN-style **5-10x faster** inference
- **RetNet**: O(1) memory per layer at inference

> "The Mamba-2 state-space duality proved SSMs and attention share a common mathematical framework."

---

# Hybrid Architectures & The Future

**The emerging consensus: pick the right tool for each subproblem**

### Hybrid designs (2024-2026):

| Model | Attention | SSM | MoE |
|-------|:---------:|:---:|:---:|
| **Jamba** (AI21) | Yes | Yes (Mamba) | Yes |
| **Samba** (Microsoft) | Yes | Yes (Mamba) | — |
| **StripedHyena** (Together) | Yes | Gated conv | — |

### Industry trends (2025-2026):
1. **Massive MoE deployment**: GPT-4, Gemini, Claude all use MoE at scale
2. **1M+ token contexts**: Long-context becoming standard
3. **Architecture convergence**: Attention + SSM hybrids as new default
4. **Hardware co-design**: Architectures optimized for specific inference chips
5. **Distilled specialists**: Small dense models distilled from large MoE teachers

---

# Key Takeaways

### The evolution trajectory:

```
2017: Dense Transformer ← "One architecture dominates all"
2022: Sparse MoE       ← "Activate only what you need"
2024: SSM / Linear     ← "Escape the quadratic bottleneck"
2026: Hybrid           ← "Best mechanism for each subproblem"
```

### Three principles:

1. **Sparsity is the unifying theme** — from data to parameters to compute
2. **No more monoculture** — modern models combine attention + SSM + MoE
3. **The field is converging** — attention and SSMs share a common mathematical foundation

---

<!-- _class: invert -->

# <!-- fit --> Thank You

**References:** wiki articles on [[transformer-architecture]], [[mixture-of-experts]], [[moe-evolution]], [[post-moe-trends]]

*Generated from the LLM Knowledge Base — 2026-06-02*
