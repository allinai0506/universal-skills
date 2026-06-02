# Wiki Health Check Report

**Wiki:** ML Architecture Research Wiki
**Location:** `wiki/`
**Scan Date:** 2026-06-02
**Pages Scanned:** 8 (index + 4 content + 2 articles + 1 connection + 1 metadata)

---

## Executive Summary

| Check | Status | Count | Severity |
|-------|--------|-------|----------|
| Broken Backlinks | FAIL | 3 broken links | High |
| Orphan Pages | FAIL | 1 orphan page | High |
| Missing Provenance | FAIL | 2 pages missing `sources:` | Medium |
| Inconsistent Data | FAIL | 1 factual inconsistency | High |
| Gap Candidates | INFO | 5+ suggested topics | Low |
| Size Warnings | PASS | 0 oversized pages | - |

---

## 1. Broken Backlinks (HIGH PRIORITY)

Three `[[wiki-link]]` references point to pages that do not exist:

| # | Source Page | Broken Link | Referenced In |
|---|-------------|-------------|---------------|
| 1 | `concepts/mixture-of-experts.md` | `[[sparse-moe-models]]` | Line 5 (frontmatter `related:`) + Line 35 (body) |
| 2 | `concepts/quantization.md` | `[[inference-optimization]]` | Line 5 (frontmatter `related:`) |
| 3 | `connections/cross-connections.md` | `[[attention-vs-rnn]]` | Line 4 (frontmatter `related:`) + Line 28 (body) |

**Impact:** These pages cannot be navigated to via the Obsidian graph view. Two of them (`[[sparse-moe-models]]`, `[[inference-optimization]]`) represent real gaps; one (`[[attention-vs-rnn]]`) is a legitimate suggested topic.

**Recommended fix:** Either create these three pages or remove the links.

---

## 2. Orphan Page (HIGH PRIORITY)

| Page | Incoming Links | Notes |
|-----|----------------|-------|
| `concepts/quantization.md` | 1 (from `metadata/tags.md` only) | Not linked from `index.md` or any content page |

`quantization.md` is only referenced from the tag index metadata page, making it effectively orphaned from a content navigation standpoint. A reader browsing the wiki through `index.md` will never discover it.

**Recommended fix:** Add `[[quantization]]` to `index.md` under the Concepts section and/or link to it from relevant content pages (e.g., `transformer-architecture.md` currently mentions "quantization" as plain text on line 23 but does not use a `[[wiki-link]]`).

---

## 3. Missing Provenance (MEDIUM PRIORITY)

Per skill convention, every wiki article must have a `sources:` field linking back to raw source documents.

| Page | Has `sources:`? | Notes |
|------|----------------|-------|
| `concepts/transformer-architecture.md` | Yes -- `["raw/articles/moe-2024.md"]` | OK |
| `concepts/mixture-of-experts.md` | Yes -- `["raw/articles/moe-2024.md"]` | OK |
| `concepts/quantization.md` | Yes -- `["raw/articles/moe-2024.md"]` | OK |
| `articles/attention-mechanism.md` | **NO** | Has `related:` but no `sources:` |
| `articles/llm-scaling-laws.md` | Yes -- `["raw/articles/moe-2024.md"]` | OK |
| `connections/cross-connections.md` | **NO** | Has `related:` but no `sources:` |

Two pages lack provenance. This makes it impossible to trace their claims back to ingested source material.

**Recommended fix:** Add `sources:` frontmatter to both `attention-mechanism.md` and `cross-connections.md`.

---

## 4. Inconsistent Data (HIGH PRIORITY)

### Transformer Introduction Date

| Source | Claim |
|--------|-------|
| `concepts/transformer-architecture.md` (line 12) | "The Transformer architecture was introduced in **2017**" |
| `articles/attention-mechanism.md` (line 16) | "**2018** -- The Transformer architecture was introduced" |

**Verdict:** The correct date is **2017**. The paper "Attention Is All You Need" (Vaswani et al.) was published at NeurIPS 2017. The `attention-mechanism.md` page is incorrect.

**Recommended fix:** Change "2018" to "2017" in `attention-mechanism.md` line 16.

### Quantization Timeline
- `transformer-architecture.md` line 23: mentions "quantization techniques from 2023"
- `quantization.md` line 12: "first widely adopted in 2023"

**Verdict:** CONSISTENT. No action needed.

---

## 5. Gap Candidates (LOW PRIORITY / OPPORTUNITY)

Topics and concepts mentioned across the wiki that lack dedicated pages:

### Directly linked but missing (broken links becoming content):
1. **`sparse-moe-models`** -- Referenced from `mixture-of-experts.md`. Could cover the latest generation of MoE architectures (Mixtral, DeepSeek-MoE, Qwen-MoE).
2. **`inference-optimization`** -- Referenced from `quantization.md`. A natural companion article covering the broader landscape of inference speedups (speculative decoding, KV-cache optimization, prefix caching).
3. **`attention-vs-rnn`** -- Referenced from `cross-connections.md`. Historical perspective on why Transformers replaced RNNs.

### Implicit gaps (mentioned in prose, no article):
4. **Expert Parallelism** -- Mentioned in `mixture-of-experts.md` line 24. Important distributed training concept.
5. **Load Balancing in MoE** -- Mentioned in `mixture-of-experts.md` line 23. Core challenge in MoE training.
6. **Quantization Techniques Comparison** -- `quantization.md` mentions GPTQ, PTQ, QAT but has no comparative analysis article.

---

## 6. Size Warnings (PASS)

No articles exceed 50 lines. All are appropriately sized. No action needed.

---

## 7. Staleness Check

| Page | Last Updated | Days Since Update | Notes |
|------|-------------|-------------------|-------|
| `articles/llm-scaling-laws.md` | 2026-05-10 | 23 days | Newer sources discuss MoE scaling laws; not reflected here |
| `concepts/transformer-architecture.md` | 2026-05-20 | 13 days | Still current |
| `articles/attention-mechanism.md` | 2026-05-22 | 11 days | Still current |
| `concepts/quantization.md` | 2026-05-24 | 9 days | Still current |
| `concepts/mixture-of-experts.md` | 2026-05-25 | 8 days | Still current |
| `connections/cross-connections.md` | 2026-05-25 | 8 days | Still current |

`llm-scaling-laws.md` is the most stale page. Given that the newer MoE article discusses how sparse models may follow different scaling laws, this page would benefit from an update.

---

## Prioritized Action List

Please indicate which items you want addressed:

1. **[HIGH] Fix Transformer date inconsistency** -- Change "2018" to "2017" in `articles/attention-mechanism.md`
2. **[HIGH] Fix 3 broken backlinks** -- Either create `sparse-moe-models.md`, `inference-optimization.md`, and `attention-vs-rnn.md`, or remove the links
3. **[HIGH] De-orphan `concepts/quantization.md`** -- Add `[[quantization]]` to `index.md` or link from content pages
4. **[MEDIUM] Add provenance to 2 pages** -- Add `sources:` frontmatter to `attention-mechanism.md` and `cross-connections.md`
5. **[LOW] Refresh `llm-scaling-laws.md`** -- Incorporate MoE-aware scaling law perspective
6. **[LOW] Write gap articles** -- Start with the 3 broken-link pages to fix issues 2 and 5 simultaneously

---

*Report generated by `/lint` operation. Ready for user review -- I will not auto-fix without confirmation.*
