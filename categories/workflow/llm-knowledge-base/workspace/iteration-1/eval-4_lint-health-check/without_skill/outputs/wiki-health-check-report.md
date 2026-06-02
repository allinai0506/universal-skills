# LLM Knowledge Base — Health Check Report

**Date:** 2026-06-02
**Wiki Version:** Iteration 1 (Post Eval 1-3)
**Pages Checked:** 27 (6 articles, 12 concepts, 3 connections, 2 metadata, 1 index, 3 outputs)
**Total Word Count:** ~4,000+ words across wiki pages (excluding outputs)

---

## 1. Orphan Pages (Pages Not Linked From Any Other Page)

Two pages exist on disk but have zero incoming `[[wikilinks]]` from other pages:

| Page | File | Severity |
|------|------|----------|
| **Neural Routing** | `wiki/concepts/neural-routing.md` | HIGH |
| **Transformer Evolution** | `wiki/concepts/transformer-evolution.md` | HIGH |

**Neural Routing** is a well-written 51-line page covering the deep connection between attention routing and MoE routing, yet no other page links to it. Possible fix: add `[[Neural Routing]]` or `[[neural-routing]]` to relevant pages (attention-mechanism.md, mixture-of-experts.md, attention-moe-crossover.md).

**Transformer Evolution** provides a useful 2017-2026 evolution timeline. It should be linked from the index and/or from articles like transformer-architecture.md.

---

## 2. Broken Backlinks (Wiki Links to Nonexistent Pages)

The following `[[wikilinks]]` reference pages that do not exist on disk:

| Broken Link | Source Page(s) | Severity |
|------------|----------------|----------|
| `[[attention-moe-crossovers]]` *(plural)* | concepts/multi-head-attention.md, concepts/neural-routing.md, concepts/transformer-architecture.md | HIGH |
| `[[Chinchilla Scaling]]` | concepts/scaling-laws.md | HIGH |
| `[[MoE Scaling Properties]]` | concepts/scaling-laws.md, outputs/reports/attention-moe-connections.md | HIGH |
| `[[Soft MoE]]` | concepts/expert-routing.md, concepts/mixture-of-experts.md | MEDIUM |
| `[[Top-K Routing]]` | concepts/expert-routing.md | MEDIUM |
| `[[Deep Routing]]` | concepts/expert-routing.md | MEDIUM |
| `[[Dense Model]]` | concepts/mixture-of-experts.md | LOW |
| `[[Pruning]]` | concepts/sparse-activation.md | LOW |
| `[[Quantization]]` | concepts/sparse-activation.md | LOW |

**Notable:** `[[attention-moe-crossovers]]` (plural, does not exist) appears in **3 different pages** while `[[attention-moe-crossover]]` (singular, does exist as `connections/attention-moe-crossover.md`) is a different link. The plural references are all broken and should be corrected to the singular form.

---

## 3. Duplicate Content

### Critical: "Transformer Architecture" — Two Pages, Same Title

Both files exist with identical `title:` frontmatter "Transformer Architecture":

| File | Lines | Focus |
|------|-------|-------|
| `wiki/articles/transformer-architecture.md` | 51 | Comprehensive: encoder-decoder structure, scaling, limitations, legacy |
| `wiki/concepts/transformer-architecture.md` | 53 | Decoder-only focus, FFN-MoE connection, deep integration with sparsity |

**Problem:** Obsidian cannot distinguish between these two when resolving `[[Transformer Architecture]]` links. The seven pages that link to `[[Transformer Architecture]]` or `[[transformer-architecture]]` may resolve to either file, creating unpredictable navigation.

**Recommended fix:** Rename one of them. Suggestions:
- Article: `Transformer Architecture` or keep as-is for the overview
- Concept: `Transformer Design Principles` or `Transformer Architecture Deep-Dive` (with a different title)

---

## 4. Missing / Broken Provenance

### 4a. Pages Without `sources:` Field

The following pages have **no** `sources:` field at all in their frontmatter:

| Page | Severity |
|------|----------|
| `concepts/attention-mechanism.md` | HIGH |
| `concepts/mixture-of-experts.md` | HIGH |
| `concepts/scaling-laws.md` | HIGH |
| `concepts/soft-routing.md` | MEDIUM |
| `concepts/sparse-activation.md` | MEDIUM |
| `concepts/expert-routing.md` | MEDIUM (intentionally missing, per inline comment) |
| `articles/post-moe-trends.md` | MEDIUM (has `sources: []` — empty) |

Concepts should ideally link back to the raw sources or the articles they derive from.

### 4b. Pages Pointing to Raw Files That Don't Exist

The `raw/` directory itself does not exist on disk. The following pages reference raw source files that don't exist:

| Page | `sources` Reference | Missing Since |
|------|--------------------|---------------|
| `concepts/conditional-computation.md` | `raw/articles/conditional-computation-review.md` | Never ingested |
| `concepts/feedforward-networks.md` | `raw/articles/attention-is-all-you-need.md` | Never ingested |
| `concepts/multi-head-attention.md` | `raw/articles/attention-is-all-you-need.md` | Never ingested |
| `concepts/neural-routing.md` | `raw/articles/gating-and-routing-survey.md` | Never ingested |
| `concepts/transformer-architecture.md` | `raw/articles/attention-is-all-you-need.md` | Never ingested |

These concept pages were written with assumed raw sources that were never actually added to `raw/`. This makes the provenance chain incomplete.

### 4c. Pages Referencing Eval Path Instead of Raw

| Page | Current `sources` | Issue |
|------|-------------------|-------|
| `articles/moe-evolution.md` | `evals/fixtures/raw/articles/moe-2024.md` | References evals path, not `raw/` |
| `articles/transformer-architecture.md` | `evals/fixtures/raw/articles/moe-2024.md` | Same issue + this article is about Transformer, not MoE (incorrect provenance) |
| `articles/moe-architecture-overview.md` | `raw/articles/moe-2024.md` | Would be correct but `raw/` doesn't exist |

The raw source material (`moe-2024.md`) lives only in `evals/fixtures/raw/` and has never been copied to the canonical `raw/articles/` directory as required by the wiki convention.

---

## 5. Inconsistent Data

### 5a. Switch Transformer Publication Year Conflict

| Page | Claimed Year |
|------|-------------|
| `concepts/sparse-activation.md` | "established in **2020** by the Switch Transformer paper" |
| `concepts/mixture-of-experts.md` | "**2022** \| Switch Transformer (Google)" |
| `articles/moe-evolution.md` | "**2022:** Switch Transformer (Google)" |
| Raw source (`moe-2024.md`) | "Switch Transformer (Google, 2022)" |

**Verdict:** The sparse-activation page has a **factual error** — it claims 2020, while the authoritative source and all other pages agree on 2022. The Switch Transformer paper was published at NeurIPS 2022 (and preprint on arXiv in 2022).

### 5b. MoE Introduction Timeline Ambiguity

`concepts/mixture-of-experts.md` correctly acknowledges the 2017 Shazeer et al. paper as "the first modern MoE layer", while `concepts/sparse-activation.md` credits 2020/2022 Switch Transformer as the origin. These are different claims about different milestones, but presented without clarification, which could confuse readers.

### 5c. Provenance on `transformer-evolution.md`

`concepts/transformer-evolution.md` lists its sources as wiki articles rather than raw sources:
```
sources: ["wiki/articles/transformer-architecture.md", "wiki/articles/moe-evolution.md", "wiki/articles/post-moe-trends.md"]
```
This breaks the provenance chain — sources should point to `raw/`, not to other wiki pages. (Git it could be argued that this is a meta-summary page.)

---

## 6. New Topic Directions (Gap Analysis)

### High-Value New Pages (Referenced but Missing)

| Topic | Referenced From | Priority | Rationale |
|-------|----------------|----------|-----------|
| **Soft MoE** | 4+ pages reference it | HIGH | Key 2023 innovation; currently only discussed inline |
| **Chinchilla Scaling** | concepts/scaling-laws.md | HIGH | Compute-optimal scaling is critical to understanding MoE economics |
| **MoE Scaling Properties** | concepts/scaling-laws.md, outputs | HIGH | How scaling laws differ for sparse models |
| **Attention-MoE Crossovers** (dedicated deep-dive) | 3 pages link to it *(with wrong name)* | HIGH | Already partially done in connections/ but the broken links suggest demand |
| **Top-K Routing / Routing Taxonomy** | concepts/expert-routing.md | MEDIUM | Systematic comparison of routing strategies |
| **Pruning** | concepts/sparse-activation.md | MEDIUM | Related sparsity technique, good for cross-reference |
| **Quantization** | concepts/sparse-activation.md | MEDIUM | Complementary efficiency technique |
| **Mamba / SSM Architecture Deep-Dive** | articles/post-moe-trends.md | MEDIUM | Currently covered at summary level only |
| **Distributed Training for MoE** | Implied by expert-routing.md | LOW | Infrastructure challenges mentioned but not explored |
| **GPT-4 Architecture Speculation** | Industry trends section | LOW | The most famous MoE model, largely undocumented here |

### Broader Topic Gaps

- **Benchmarking methodology for sparse models** — How evaluation differs for MoE vs dense
- **Hardware co-design** — How GPU/NPU architecture influences MoE design (mentioned briefly in post-moe-trends)
- **MoE fine-tuning strategies** — Mentioned as hard, but no page on how it's actually done (LoRA, partial fine-tuning)
- **Expert visualization / interpretability** — What do individual experts actually learn?

---

## 7. Structural Observations

### Strengths
- Excellent cross-linking density — most concepts are well-connected
- Clean, consistent frontmatter format across all pages
- The `connections/` directory is a strong feature that explicitly documents relationships
- The `attention-moe-crossover.md` page (5.7KB) is a rich, well-researched synthesis
- Clear separation between articles (broader narratives) and concepts (focused definitions)
- Tag index and metadata pages provide good navigation

### Weaknesses
- No `raw/` directory at all — the entire provenance chain is broken
- Index links to `metadata/tags.md` but doesn't list its tags in the TOC
- `outputs/` isn't linked from the index or any wiki page (except via `[[Attention-MoE Connections Report]]` which doesn't resolve)
- No cross-link validation process established

### Size Assessment
All pages are within reasonable size limits:
- Largest concept: `mixture-of-experts.md` at 2,969 bytes / 58 lines
- Largest article: `post-moe-trends.md` at 3,106 bytes / 67 lines
- Largest connection: `attention-moe-crossover.md` at 5,769 bytes / 110 lines
- No pages need splitting at this scale

---

## 8. Prioritized Fix Recommendations

| Priority | Issue | Action |
|----------|-------|--------|
| **P0** | `raw/` directory doesn't exist | Create `raw/articles/` and copy `evals/fixtures/raw/articles/moe-2024.md` into it. Also add raw sources for all referenced-but-missing files. |
| **P0** | Duplicate "Transformer Architecture" title | Rename one page (likely the concept) to avoid ambiguous wikilink resolution |
| **P1** | Orphan pages (neural-routing, transformer-evolution) | Add links from index.md and relevant articles/concepts |
| **P1** | Broken `[[attention-moe-crossovers]]` (plural) links in 3 pages | Fix to `[[attention-moe-crossover]]` (singular, existing) |
| **P1** | Sparse Activation claims 2020 instead of 2022 for Switch Transformer | Correct the factual error |
| **P2** | Missing provenance on 7 concept pages | Add `sources:` frontmatter referencing raw/ or article sources |
| **P2** | Broken backlinks to `[[Chinchilla Scaling]]`, `[[MoE Scaling Properties]]`, `[[Soft MoE]]` | Either create these pages or remove the links |
| **P3** | transformer-evolution.md references wiki pages as sources | Restructure to reference raw sources where possible |
| **P3** | Output report links not connected to wiki index | Add `[[Attention-MoE Crossover Analysis]]` entry to index |

---

## Health Score: 7/10

The wiki has strong structural foundations (clean frontmatter, good cross-linking, well-organized), but suffers from **provenance rot** (missing `raw/` directory, phantom raw sources) and a handful of **broken links and factual inaccuracies** that compound as the wiki grows. The top priority fix is establishing the `raw/` directory with actual source files, which will stop the provenance rot from spreading further.
