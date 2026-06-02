---
title: "Cross-Connections: Attention and MoE"
tags: [connection, synthesis]
related: ["[[transformer-architecture]]", "[[mixture-of-experts]]", "[[attention-mechanism]]", "[[attention-vs-rnn]]"]
created: 2026-05-21
updated: 2026-05-25
---

# Cross-Connections: Attention and MoE

This file maps the relationship between attention mechanisms and mixture of experts architectures.

## Shared Principles

Both attention and MoE use a learned **routing** mechanism:
- **Attention** routes information through weighted summation of value vectors
- **MoE** routes tokens through selected expert sub-networks

## Complementarity

In modern LLMs, attention and MoE serve different roles:
1. **Attention layers** handle cross-token communication and contextual understanding
2. **MoE feed-forward layers** expand model capacity without proportional compute increase
3. They stack in alternating patterns: Attention → MoE-FFN → Attention → MoE-FFN

## Historical Context

The [[attention-vs-rnn]] debate was a precursor to today's architecture decisions. While Transformers won over RNNs for most tasks, understanding that history informs current questions about whether MoE will similarly displace dense transformers.

## Research Directions

- Can attention itself be made sparse in an MoE-like fashion?
- Do MoE models develop "expert specialization" that mirrors attention head specialization?
- What happens when we apply MoE-style routing to attention heads?

## Key Takeaway

Attention and MoE address different bottlenecks — communication vs. computation — and are more powerful together than either alone.
