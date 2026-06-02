# Implementation Notes — MoE Knowledge Base Ingest & Compile

## Summary
Ingested the MoE 2024 article and compiled a structured wiki with 1 article, 4 concept pages, 1 connections page, and 1 index.

## Decisions & Tradeoffs

### Concept Granularity
- **Decision**: Created 4 concept pages (MoE, Sparse Activation, Expert Routing, Soft MoE) rather than lumping everything into one.
- **Rationale**: The article covers multiple distinct ideas that each benefit from their own page with backlinks. Soft MoE in particular is a philosophically different approach that deserves standalone treatment.

### Article vs. Concept Overlap
- **Decision**: The article page (`mixture-of-experts-2024.md`) focuses on the chronological survey and the 2024 breakthrough. The concept page (`mixture-of-experts.md`) focuses on the architectural pattern itself (definition, characteristics, tradeoffs).
- **Tradeoff**: Some redundancy between the two, but they serve different purposes — the article is a source-specific summary, the concept is a general reference.

### Routing Classification
- **Decision**: Categorized expert routing into three types: hard, soft, and dynamic selection.
- **Note**: The 2024 breakthrough's "dynamic selection" doesn't fit neatly into the hard vs. soft binary. I gave it its own category, which is a judgment call not explicit in the source.

### Index Scope
- **Decision**: Scoped the index to just the MoE topic since this is a single-article ingest. The skill mentions a broader wiki, but since this is the first (or an incremental) addition, I kept it focused.
- **Tradeoff**: If other transformer articles exist elsewhere in the wiki, the index would need merging. For this isolated eval, standalone is cleaner.

### What Wasn't in the Spec
- The skill says to download images to `raw/images/` — the source article has no images.
- The skill mentions optional "trigger a targeted compile" — I did the compile directly since the user asked for it.
- The skill's `wiki/concepts/` path doesn't specify granularity rules. I chose fine-grained concept extraction (4 pages) to maximize backlink connectivity.
