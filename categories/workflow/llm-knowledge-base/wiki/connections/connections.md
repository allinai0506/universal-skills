---
title: "Cross-Concept Connections"
tags: [connections, graph, relationships]
created: 2026-06-02
updated: 2026-06-02
---

# Cross-Concept Connections

## Attention + MoE

The combination of attention and Mixture of Experts is the foundation of modern sparse Transformer models. The attention layer captures token-to-token dependencies while MoE layers provide efficient feed-forward computation.

**Connected pages:** [[Mixture of Experts: Scaling Transformer Models Beyond Dense Limits]], [[Mixture of Experts]], [[Attention Mechanism]]

## Sparse Activation + Scaling Laws

The sparse activation property of MoE models fundamentally changes how scaling laws apply. Since only a fraction of parameters activate per token, the compute-to-parameter ratio is different from dense models.

**Connected pages:** [[Sparse Activation]], [[Mixture of Experts]]

## Expert Routing + Efficiency

The routing strategy directly determines both computational efficiency and model quality. Soft routing (Soft MoE) offers the best load balance at the cost of extra computation.

**Connected pages:** [[Expert Routing]], [[Sparse Activation]]
