---
title: "Expert Collapse"
tags: [concept, moe, failure-mode, routing]
related:
  - "[[mixture-of-experts]]"
  - "[[expert-routing]]"
  - "[[top-k-routing]]"
created: 2026-06-02
updated: 2026-06-02
---

# Expert Collapse

Expert collapse (also called "dying experts") is a failure mode in MoE architectures where some experts stop being selected by the router and consequently receive no gradient updates.

## Mechanism

In top-k routing, the router learns to dispatch tokens to a subset of experts that perform well. Experts that are rarely selected receive:

1. **No gradient**: The router's gating function doesn't route tokens to them
2. **No learning**: Without gradient, these experts cannot improve
3. **Collapse**: The expert becomes permanently unused, wasting parameters

## Parallels to Attention Head Collapse

Expert collapse is directly analogous to **attention head collapse** — where multiple attention heads learn the same pattern and become redundant. Both phenomena:

- Result from specialization patterns converging
- Indicate wasted capacity
- Require auxiliary regularization to prevent

## Mitigation Strategies

- **Load balancing loss**: Penalizes uneven token distribution across experts
- **Expert dropout**: Randomly drops top-k routed tokens, forcing exploration of alternative experts
- **Soft routing**: Eliminates the hard top-k boundary
- **Expert choice routing**: Lets experts choose tokens, ensuring all experts get work

## Connections

- [[mixture-of-experts]] — MoE architecture
- [[expert-routing]] — Routing strategies that can mitigate collapse
- [[top-k-routing]] — The routing variant most prone to collapse
