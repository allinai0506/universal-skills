---
title: "Connections Needed: Documented Wiki Gaps"
tags: [metadata, gaps, broken-links, todo]
created: 2026-06-02
updated: 2026-06-02
---

# Connections Needed: Documented Wiki Gaps

This page documents known gaps and broken cross-references in the wiki.

## Recently Filled Gaps

These gaps (identified during the attention-MoE crossover analysis) have been filled:

| Page | Status | Created By |
|------|--------|------------|
| `concepts/soft-moe.md` | NOW EXISTS | This workflow |
| `concepts/top-k-routing.md` | NOW EXISTS | Wiki maintenance |
| `concepts/deep-routing.md` | NOW EXISTS | Wiki maintenance |
| `concepts/moe-scaling-properties.md` | NOW EXISTS | Wiki maintenance |

Also created: `connections/gaps-and-supplements.md` — documents additional cross-connections (attention-expert-routing, conditional-computation-sparse-activation, multi-head-attention-moe, soft-expert-routing spectrum).

## Still Missing

### Broken Cross-References

| Source page | Broken link | Suggested target |
|-------------|-------------|------------------|
| `concepts/scaling-laws.md` | [[Chinchilla Scaling]] | Needs a dedicated Chinchilla scaling laws page |
| `concepts/scaling-laws.md` | [[MoE Scaling Properties]] | NOW EXISTS (concepts/moe-scaling-properties.md) — check if link resolves |

### Suggested New Pages

| Page | Priority | Rationale |
|------|----------|-----------|
| `concepts/chinchilla-scaling.md` | High | Referenced by scaling-laws.md; foundational concept for understanding compute-optimal training |
| `concepts/linear-attention.md` | Low | Mentioned in post-moe-trends.md; context for the broader efficiency landscape |
| `concepts/state-space-models.md` | Low | Core concept for post-MoE trends; currently only covered in articles |
| `articles/jamba-hybrid.md` | Medium | Jamba (attention + SSM + MoE) is the canonical "hybrid of hybrids" |
