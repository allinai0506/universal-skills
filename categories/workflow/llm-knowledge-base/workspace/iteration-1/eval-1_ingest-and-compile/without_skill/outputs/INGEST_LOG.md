# Ingest Log

## Source

- **File**: `raw/articles/moe-2024.md`
- **Title**: Mixture of Experts: Scaling Transformer Models Beyond Dense Limits
- **Source URL**: https://example.com/moe-2024-survey
- **Date Ingested**: 2026-06-02
- **Tags**: transformer, MoE, efficiency, sparsity

## Ingest Notes

- The raw article was already present in `raw/articles/moe-2024.md` with proper frontmatter metadata.
- No images were referenced in the article (images array was empty).
- The article is a survey-style piece covering 2022-2024 MoE innovations.

## Compile Summary

The following wiki pages were created:

| File | Type | Description |
|------|------|-------------|
| `wiki/articles/moe-2024.md` | Article | Full compiled wiki article with backlinks |
| `wiki/concepts/sparse-activation.md` | Concept | Core concept: sparse activation ratio and techniques |
| `wiki/concepts/expert-routing.md` | Concept | Core concept: routing strategies (hard, soft, dynamic) |
| `wiki/connections/moe-timeline-2022-2024.md` | Connection | Visual timeline connecting all MoE innovations |
| `wiki/index.md` | Index | Updated table of contents with tags index |

## Open Questions / Follow-ups

1. What specific benchmarks were used to evaluate Google's 2024 MoE? The article did not provide benchmark numbers for the 2024 breakthrough.
2. How does the "compatibility score" routing differ mathematically from a learned router? The article mentions the approach but does not give details.
3. What hardware was used for the staged training runs? Not specified in the source.
4. Are there open-source implementations of the dynamic expert selection technique? Not mentioned.
5. How does the 3x improvement generalize to different model scales? The article focuses on one result.

## Suggested Future Ingests

- "Efficient Transformers" survey (2023) — mentioned as related work, would provide broader context.
- "Sparse Model Training" paper from Google Brain — mentioned as related work.
- DeepSeek-MoE (if available) — a notable 2024 MoE variant not covered in this survey.
