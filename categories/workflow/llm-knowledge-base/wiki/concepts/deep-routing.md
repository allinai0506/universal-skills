---
title: "Deep Routing"
tags: [concept, routing, experimental]
related:
  - "[[expert-routing]]"
  - "[[mixture-of-experts]]"
  - "[[attention-mechanism]]"
created: 2026-06-02
updated: 2026-06-02
---

# Deep Routing

Deep Routing is an emerging paradigm for end-to-end learned routing policies in neural networks, extending beyond simple top-k or soft gating.

## Overview

Unlike static routing strategies (top-k, soft) or learned linear routers, Deep Routing uses deeper networks to compute routing decisions, potentially enabling:

- **Context-aware routing**: Routing decisions that consider not just the current token but its surrounding context
- **Multi-hop routing**: Tokens passing through multiple experts in sequence
- **Adaptive expert capacity**: Dynamically adjusting how many tokens each expert processes

## Status

This remains an experimental area. Standard MoE architectures (Switch Transformer, Mixtral) use simple linear routers. Deep Routing proposes replacing these with more sophisticated routing policies, but practical benefits at scale have not yet been demonstrated.

## Connections

- [[expert-routing]] — The broader routing taxonomy this belongs to
- [[attention-mechanism]] — Attention as a potential deep routing mechanism
