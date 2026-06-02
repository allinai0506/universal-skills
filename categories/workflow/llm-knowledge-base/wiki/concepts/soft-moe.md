---
title: "Soft MoE"
tags: [moe, routing, soft-routing, attention]
related: [["Mixture of Experts"], ["Attention Mechanism"], ["Soft Routing"], ["Expert Routing"]]
created: 2026-06-02
updated: 2026-06-02
---

# Soft MoE

Soft MoE (Puigcerver et al., Google, 2023) is a variant of Mixture of Experts that replaces discrete top-k routing with **continuous, attention-like soft assignment**. It is arguably the most direct architectural bridge between [[attention-mechanism]] and [[mixture-of-experts]].

## Core Idea

Instead of routing each token to exactly k experts, Soft MoE computes a weighted combination over **all** experts for each token:

1. **Slot creation**: A fixed number of "slots" per expert are initialized as learned parameters
2. **Slot assignment (attention-style)**: Each token computes affinities with all expert slots via a learned linear projection — structurally identical to attention's QK^T computation
3. **Weighted dispatch**: Each expert processes a weighted combination of tokens, where weights come from the slot affinities
4. **Weighted collection**: The output is a weighted combination of expert outputs, using the same affinity weights

## Why It Matters for the Attention-MoE Connection

Soft MoE demonstrates that the boundary between attention and MoE is artificial:

| Mechanism | Attention | Soft MoE |
|-----------|-----------|----------|
| Affinity computation | QK^T between tokens | Learned projection between tokens and expert slots |
| Softmax dimension | Over token positions | Over expert slots |
| Weighted combination | Of value vectors | Of expert outputs |
| Differentiability | Fully differentiable | Fully differentiable |

Soft MoE essentially makes the MoE router behave like **attention over experts**, where each expert is analogous to an attention head.

## Advantages Over Hard Routing

- **No load balancing loss required** — because every expert processes a weighted combination of all tokens, there are no discrete dispatch decisions to balance
- **No expert collapse** — all experts always receive gradient signal because every token contributes to every expert
- **Better gradient flow** — the routing decision is fully differentiable end-to-end
- **Simpler training** — no auxiliary losses needed

## Tradeoffs

- **Higher computational overhead** — because tokens are dense combinations rather than sparse dispatches, the expert computation is effectively dense
- **Not purely sparse** — the "soft" part eliminates the sparsity guarantee, though the per-expert computation can be made efficient through capacity limits

## Connections

- The most direct architectural bridge between [[attention-mechanism]] and [[mixture-of-experts]]
- A concrete instantiation of the [[soft-routing]] paradigm
- Demonstrates the [[conditional-computation]] principle without discrete decisions
- The slot-based mechanism parallels multi-head attention's multi-slot design
