---
title: "Attention-MoE Crossover: Connections Between Two Routing Paradigms"
tags: [attention, moe, routing, crossover]
created: 2026-06-02
updated: 2026-06-02
---

# Attention-MoE Crossover

This page documents the connections between [[attention-mechanism]] and [[mixture-of-experts]] — two mechanisms that, at their core, solve the same problem through different lenses.

## Structural Parallels

### Routing as a Unifying Concept

Both attention and MoE are **routing mechanisms**:

| Dimension | Attention | MoE |
|-----------|-----------|-----|
| What is routed | Token values to other token positions | Token representations to expert sub-networks |
| Routing function | QK^T compatibility (dense) | Gating network (sparse) |
| Weighted combination | Softmax over keys → weighted sum of values | Softmax over experts → weighted sum of expert outputs |
| Output | Contextualized token | Transformed token |

The mathematical formulations are strikingly parallel:

**Attention**: 
$$y_i = \sum_j \text{softmax}_j(q_i^T k_j / \sqrt{d}) \cdot v_j$$

**MoE**:
$$y = \sum_i \text{softmax}_i(G(x))_i \cdot E_i(x)$$

Both compute a softmax-based probability distribution and return a weighted combination. The difference is **what** is being weighted: token positions (attention) vs. expert functions (MoE).

## Direct Crossover Work

### 1. Soft MoE (Google, 2023)
Replaces discrete top-k MoE routing with an **attention-like assignment** where each token is a weighted combination of all experts. The slot-to-expert assignment uses a learned linear layer analogous to attention QKV projections.

**Connection**: This is arguably the closest architectural bridge — MoE routing becomes attention.

### 2. Switch Transformers (Google, 2022)
Top-1 routing can be viewed as **hard attention over experts**. The router computes a distribution and selects the argmax — structurally identical to hard attention mechanisms.

**Connection**: Demonstrates the softmax-over-options pattern unifying both methods.

### 3. Multi-Head Attention as Expert Collection
Each attention head can be viewed as an "expert" focusing on different relationship types (syntax, semantics, position). The concatenation of heads parallels the ensemble of experts in MoE, with the output projection W^O serving as a learned combiner.

### 4. Expert Choice Routing (Google, 2022)
Instead of having routers choose experts for each token, experts choose which tokens to process. This is an **inverse attention** — in attention, queries (tokens) compute affinity with keys (positions); in expert choice, experts compute affinity with tokens.

### 5. Mixture of Attentions (Various)
Several works explore using multiple attention mechanisms as experts:
- **Mixture of Attention Heads**: Each head learns different attention patterns
- **Attention MoE**: Routing tokens to different attention mechanisms based on content
- **Sparse Attention with Expert Heads**: Different heads handle different token types

### 6. Unified Formulations
Some theoretical works propose unified frameworks where attention and MoE are instances of a broader **learned routing** paradigm:
- **Hypernetworks** that generate both attention weights and expert weights
- **Conditional computation** frameworks where both attention masking and expert selection are forms of conditional computation
- **Token-level routing decisions** that jointly determine attention patterns and expert selection

## Theoretical Connections

### Shared Origins: Conditional Computation

Both attention and MoE trace back to the concept of **conditional computation** — where which computations are performed depends on the input:

- MoE: "Which experts should process this token?"
- Attention: "Which tokens should this token interact with?"

### The Routing-Sparsity Tradeoff

- **Attention** has no parameter sparsity (all FFN params used per token) but selective interaction (not all token pairs equally important)
- **MoE** has full interaction (through the single remaining dense attention layer) but selective parameter activation

This suggests their combination is **naturally complementary rather than competitive**.

### Multiplicity Pattern

Both mechanisms use the **"multiple copies with gating"** pattern:
- Attention: Multi-head = multiple attention copies + concat + projection
- MoE: Multi-expert = multiple FFN copies + weighted sum

## Research Gaps

### Underexplored Connections

1. **End-to-end differentiable routing**: Could we have a single routing mechanism that jointly determines both attention patterns and expert selection? This would unify the two mechanisms but faces computational challenges.

2. **Cross-layer MoE with attention conditioning**: Should expert selection be conditioned on attention outputs (as it is now) or should expert selection influence attention patterns?

3. **Dynamic expert creation via attention**: Could attention reveal latent clusters/expert specializations, enabling dynamic expert creation during training?

4. **Attention-as-expert**: If each expert is an FFN, could an "expert" be an entire attention sub-layer? This would create mixtures over different attention mechanisms.

### Open Questions

- Could attention-based routing replace learned gating entirely in MoE layers?
- Is the standard "dense attention + sparse MoE" split optimal, or should both be sparse?
- What happens if we reverse the roles: sparse attention + dense MoE?
- How do scaling laws change when both dimensions are tuned jointly?

## Connections Added to Wiki

- [[attention-mechanism]] ↔ [[mixture-of-experts]] — Core routing parallelism
- [[soft-routing]] — Bridges the discrete-continuous gap between hard MoE and attention
- [[sparse-activation]] — The common sparsity framing
