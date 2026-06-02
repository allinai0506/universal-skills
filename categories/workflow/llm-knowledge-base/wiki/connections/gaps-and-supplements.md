---
title: "Gaps and Supplements: Attention-MoE Crossover"
tags: [connections, gaps, supplements, crossover]
created: 2026-06-02
updated: 2026-06-02
---

# Gaps and Supplements: Attention-MoE Crossover

This page documents connections and gaps identified during the query workflow.

## New Connections Identified

### 1. Attention ↔ Expert Routing (Deeper Than Documented)

**Connection type:** Shared paradigm

Both [[attention-mechanism]] and [[expert-routing]] solve the same problem: "which computation for which input?" The attention softmax over keys and the MoE router softmax over experts use mathematically identical operations. Key distinction: attention uses softmax (all positions, dense), MoE uses softmax + top-k (sparse selection).

**Evidence:** The softmax(QK^T) in attention and softmax(W_r · x) in MoE routers are structurally identical. Both are learned content-based routing with differentiable gates.

### 2. Conditional Computation ↔ Sparse Activation (Unifying Framework)

**Connection type:** Theory unification

[[conditional-computation]] is the abstract framework; [[sparse-activation]] is the concrete implementation. Both attention (via softmax masking/gating) and MoE (via top-k routing) implement conditional computation — the input determines which computations execute.

**Evidence:** Bengio (2013) on stochastic neurons → Shazeer (2017) on MoE → contemporary sparse attention works all trace to conditional computation.

### 3. Multi-Head Attention ↔ Mixture of Experts (Multi-Copy Pattern)

**Connection type:** Architectural isomorphism

Both use the same pattern: create multiple specialized copies, combine results with learned weights. In [[multi-head-attention]], heads are always dense and combined via concat + projection. In [[mixture-of-experts]], experts are sparse and combined via weighted sum from a router.

**Evidence:** If you apply top-k sparsity to attention heads (i.e., only activate k heads per token), you get a direct MoE analog. This is exactly what routing-based sparse attention does.

### 4. Soft Routing ↔ Expert Routing (Soft-Hard Spectrum)

**Connection type:** Spectrum

[[soft-routing]] (attention style) and [[expert-routing]] (MoE style) represent two ends of a spectrum. In the middle: Soft MoE (soft assignment over experts) and sparse attention (hard top-k over token positions).

**Evidence:** Soft MoE uses attention-like assignment over experts. Sparse attention (Routing Transformer, BigBird) uses MoE-like top-k over token positions.

## New Connections Added to Wiki

The following crosslinks have been added or strengthened:

- [[attention-mechanism]] ↔ [[expert-routing]] — Shared routing paradigm
- [[conditional-computation]] ↔ [[sparse-activation]] — Implementation of conditional computation
- [[multi-head-attention]] ↔ [[mixture-of-experts]] — Multi-copy architecture pattern
- [[soft-routing]] ↔ [[expert-routing]] — Opposite ends of the routing spectrum

## Open Questions from Query

1. **Does FlashAttention change MoE+Attention joint optimization?** FlashAttention makes attention cheaper, which might shift the optimal sparse/dense boundary.

2. **Can we route to both attention positions AND experts with a single router?** Current architecture separates these decisions. A unified router could optimize the joint token-expert assignment.

3. **What does the scaling law surface look like for joint attention-head × expert-count optimization?** No published work yet.

4. **Do attention head collapse and expert collapse share a mechanism?** Both involve specialization patterns collapsing — possibly same underlying dynamics.

## References

- Full analysis report: [[attention-moe-crossover-analysis]]
- Prior crossover documentation: [[attention-moe-crossover]]
- Architecture connections: [[llm-architecture-connections]]
