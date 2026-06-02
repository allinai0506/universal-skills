---
title: "Connections: LLM Architecture Evolution"
tags: [connections, cross-reference]
created: 2026-06-02
updated: 2026-06-02
---

# Connections: LLM Architecture Evolution

## Attention ↔ MoE

**Link type:** Complementary orthogonal innovations

Attention and MoE solve fundamentally different bottlenecks:
- Attention addresses the **communication** bottleneck — how tokens exchange information
- MoE addresses the **capacity** bottleneck — how many parameters contribute per token

**Evidence:** GPT-4, Gemini, and Mixtral all use both attention and MoE. They are not competing mechanisms but complementary ones. Attention handles cross-token interactions; MoE scales up the feed-forward capacity.

## Dense → Sparse Trajectory

**Link type:** Industry trend

The trajectory of LLM architecture evolution is clear: **dense → sparse → selective**.

1. **2017-2022:** Dense Transformers (every parameter active for every token)
2. **2022-2024:** Sparse via MoE (subset of parameters active via routing)
3. **2024-2026:** Selective via learned mechanisms (SSMs choose what to remember, attention chooses what to focus on)

**Evidence:** The progression from GPT-3 (dense) → Mixtral (sparse MoE) → Mamba (selective SSM) shows this trajectory clearly.

## SSM → Attention Connection

**Link type:** Mathematical equivalence (Mamba-2)

The Mamba-2 paper (Dao & Gu, 2024) proved a "state space duality" showing that SSMs and attention share a common mathematical framework. This means:
- Improvements in SSM training directly benefit attention variants
- Hybrid architectures can be analyzed with a unified theory
- The future architecture might be neither pure attention nor pure SSM

## Key Insight

The architecture landscape is fragmenting: no single architecture dominates. Instead, models increasingly combine multiple mechanisms (attention + SSM + MoE) in hybrid designs that pick the right tool for each subproblem.
