---
title: "Expert Routing"
tags: [concept, moe, routing, mechanism]
sources: ["raw/articles/moe-2024.md"]
related: ["[[Mixture of Experts]]", "[[Soft MoE]]", "[[Sparse Activation]]"]
created: 2026-06-02
updated: 2026-06-02
---

# Expert Routing

## Definition

Expert routing is the mechanism by which a Mixture of Experts model decides which experts to activate for each input token. The routing strategy is the central design decision in MoE architectures, directly impacting model quality, computational efficiency, and training stability.

## Routing Types

### Hard Routing (Discrete)
Each token is routed to a fixed number of top-scoring experts (typically 1 or 2).

- **Switch Transformer**: Top-1 routing — simplest, enables scaling to 2048 experts
- **Mixtral 8x7B**: Top-2 routing — better quality than top-1 at moderate expert counts
- **Challenge**: Load balancing — some experts may receive disproportionately many tokens

### Soft Routing (Continuous)
Each token is a weighted combination of all experts, with learned weights.

- **Soft MoE (Google, 2023)**: Replaces discrete selection with soft assignment
- **Advantage**: Eliminates load balancing loss entirely; better gradient flow
- **Tradeoff**: All expert weights still need to be in memory and contribute to computation

### Dynamic Selection (2024 Breakthrough)
A compatibility score is computed between each token and expert representation, without a traditional learned router.

- **Advantage**: More flexible routing that can adapt to token complexity
- **Key enabler**: Combined with expert specialization pressure and staged training

## Key Challenges

- **Load balancing**: Ensuring all experts receive sufficient training signal
- **Expert collapse**: When experts become unused (dead experts)
- **Routing stability**: Consistent expert assignments across training steps
- **Communication overhead**: In distributed training, routing decisions require all-to-all communication

## Connections

- Expert routing is the core mechanism of [[Mixture of Experts]] architectures
- Different routing strategies directly affect the [[Sparse Activation]] ratio
- [[Soft MoE]] represents the soft routing paradigm in its purest form
