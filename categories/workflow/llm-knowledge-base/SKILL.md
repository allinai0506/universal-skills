---
name: llm-knowledge-base
description: >
  Full-stack LLM-driven knowledge base management with Obsidian integration —
  ingest raw sources → compile into structured wiki → Q&A → generate outputs
  (markdown, Marp slides, matplotlib) → lint for consistency → file results back.
  Trigger when user mentions: knowledge base, research wiki, Obsidian, compiling
  research notes, managing a wiki with LLM, "kb", personal knowledge base, PKM
  workflow, building a wiki from sources, or any workflow involving raw/
  directories and compiled markdown wikis. Also trigger when the user wants to
  organize scattered documents, build a research knowledge base, or create a
  self-compounding knowledge system.

  This is an important skill — it captures a workflow where the LLM acts as the
  primary writer/maintainer of a knowledge base while the user curates via Obsidian.
  Use it whenever you detect knowledge management intent, even if the user doesn't
  explicitly name the skill.
---

# LLM Knowledge Base

A workflow for building and maintaining a **personal knowledge base** using an LLM as the primary compiler, writer, and curator — with Obsidian as the visual frontend.

## Philosophy

The key insight: **the LLM writes and maintains the wiki.** The user rarely touches markdown files directly. Instead:

1. **User collects** raw source material (articles, papers, datasets, images) into `raw/`
2. **LLM compiles** the raw material into a structured `.md` wiki — summaries, concepts, articles, backlinks
3. **User views** everything in Obsidian (the "IDE frontend")
4. **LLM answers questions** against the wiki and files outputs back
5. **Knowledge compounds** — every query adds to the wiki

## Directory Convention

```
<project>/
├── raw/                        # Source documents (articles, PDFs, images, datasets)
│   ├── articles/
│   ├── papers/
│   ├── datasets/
│   └── images/                 # Downloaded for LLM reference
├── wiki/                       # Compiled knowledge base (LLM-written)
│   ├── index.md                # Auto-maintained table of contents
│   ├── concepts/               # Concept articles with backlinks
│   ├── articles/               # Full article summaries
│   ├── connections/            # Cross-article links and relationships
│   └── metadata/               # Tags, categories, provenance
├── outputs/                    # Generated outputs (LLM-written)
│   ├── slides/                 # Marp-format slide decks
│   ├── figures/                # matplotlib/pyplot figures
│   └── reports/                # Analytical reports
└── tools/                      # Optional helper scripts
    └── search.py               # Simple search engine over the wiki
```

## Operations

### 1. Ingest (`/ingest`)

Process new source documents into the knowledge base.

**User says:** "I found this article about X, add it to my research"

**You do:**
1. Accept the source (URL, file path, pasted text, or Obsidian Web Clipper export)
2. Save the raw source to `raw/articles/<topic>-<date>.md` with provenance metadata
3. If images are referenced, download them to `raw/images/` so you can reference them
4. Optionally trigger a targeted compile for this new source (see Compile)

**Web Clipper workflow:** When the user mentions using Obsidian Web Clipper, the raw article `.md` is typically already in `raw/`. Your job is to summarize it, extract key concepts, and integrate it into the wiki.

**Metadata to capture in raw files:**

```yaml
---
title: "Article Title"
source: "URL or DOI"
date_ingested: 2026-06-02
tags: ["relevant", "tags"]
images: ["raw/images/figure-1.png"]
---
```

### 2. Compile (`/compile`)

The core operation — transform raw material into a structured, interconnected wiki.

**User says:** "Compile my research on topic X into the wiki"

**You do:**
1. **Scan** `raw/` for documents related to the topic
2. **Summarize** each source as a wiki article under `wiki/articles/`
3. **Extract concepts** — identify key concepts/entities and write concept pages under `wiki/concepts/`
4. **Build connections** — identify relationships between concepts, create backlinks using `[[wiki-link]]` syntax
5. **Update index** — refresh `wiki/index.md` with the new content
6. **Provenance** — each article should link back to its source(s) in `raw/`

The compile step is incremental. When new sources arrive, you don't rewrite everything — you update affected articles and create new ones.

**Wiki article format:**
```markdown
---
title: "Topic Title"
tags: [concept, research-area]
sources: ["raw/articles/source-1.md", "raw/articles/source-2.md"]
related: ["[[Related Concept]]", "[[Related Article]]"]
created: 2026-06-02
updated: 2026-06-02
---

# Topic Title

Summary of the concept/article...

## Key Points

- Point 1
- Point 2

## Connections

Related to [[Another Concept]] via shared property X.

## Source Summary

Brief provenance of this knowledge.
```

### 3. Query & Research (`/query`)

Ask complex questions against the wiki. No RAG needed at this scale — the LLM reads relevant files directly.

**User says:** "What does my research say about topic X and its relationship to Y?"

**You do:**
1. **Read the index** (`wiki/index.md`) to find relevant pages
2. **Read the relevant pages** from `wiki/articles/` and `wiki/concepts/`
3. **Synthesize** an answer with citations back to specific wiki pages and raw sources
4. **Optionally file the answer** back into the wiki as a new article or connection (recommended)

Key behavior: every Q&A session should ideally leave the wiki more complete than before. If the answer reveals a new connection, add it to `wiki/connections/`. If the answer covers territory not yet in the wiki, write a new article.

**When the wiki is large** (100+ articles, 400K+ words): The LLM should rely on the index file and summary metadata to locate relevant pages before reading them in full. The wiki's structure (concepts, connections, backlinks) is designed to make this efficient without vector search.

### 4. Output (`/output`)

Generate polished deliverables from the wiki.

**User says:** "Turn my research on X into a presentation" or "Visualize the relationship between these concepts"

**You do:**

| Output Format | How | View In |
|---|---|---|
| Markdown report | Write to `outputs/reports/` | Obsidian |
| Marp slides | Write Marp-format `.md` with `---` slide separators to `outputs/slides/` | Obsidian + Marp plugin |
| matplotlib figure | Write Python script, execute, save `.png` to `outputs/figures/` | Obsidian (image embed) |
| Knowledge graph | Generate a graphviz `.dot` or mermaid diagram, render to `outputs/figures/` | Obsidian |

**Marp format example:**
```markdown
---
marp: true
theme: default
---

# Research Title

Author: LLM-generated

---

## Key Finding

- Finding 1
- Finding 2

---

![Figure](outputs/figures/relationship-diagram.png)
```

### 5. Lint & Health Check (`/lint`)

Run integrity checks on the wiki to maintain quality.

**User says:** "Check my wiki for issues" or "Lint the knowledge base"

**You check for:**

- **Orphan pages** — articles not linked from any other page
- **Stale content** — articles not updated after new relevant sources were ingested
- **Broken backlinks** — `[[wiki-link]]` references to nonexistent pages
- **Inconsistent data** — conflicting information across articles (e.g., two articles claiming different dates for the same event)
- **Missing provenance** — articles without `sources:` links back to `raw/`
- **Gap candidates** — topics suggested by cross-referencing that don't have articles yet
- **Size warnings** — articles approaching unmanageable length (suggest splitting)

**After linting:** Present a prioritized fix list. Don't auto-fix everything — ask the user which items to address. Use web search when needed to resolve inconsistencies with external sources.

### 6. Enhance (`/enhance`)

Suggest improvements to the knowledge base structure and coverage.

**User says:** "What should I add to my wiki?" or "Find interesting connections"

**You do:**
1. **Cross-reference** all articles to find latent connections
2. **Suggest new article ideas** — topics implied by existing content but not yet written
3. **Recommend further reading** — based on coverage gaps
4. **Propose structural improvements** — new categories, better organization

## Obsidian Integration

Obsidian is the "IDE frontend" for the knowledge base. Follow these conventions:

- **Wiki links:** Use `[[page-name]]` syntax for all cross-references (Obsidian-native)
- **Image embeds:** Use `![description](outputs/figures/file.png)` (Obsidian renders these inline)
- **Tags:** Use `#tag` syntax inline or `tags:` in frontmatter
- **Marp:** Slides with Marp frontmatter render natively in Obsidian with the Marp plugin
- **Graph View:** Obsidian's built-in graph view works with `[[wiki-link]]` syntax automatically
- **No Obsidian-specific plugins required** beyond what the user mentions — the skill uses plain markdown

## Tooling: Search Engine

When the wiki grows large, a dedicated search tool helps. The user may have vibe-coded one already. Use it when available:

```bash
python3 tools/search.py --query "your search terms" --wiki-path wiki/
```

If no search tool exists but the wiki is large enough to warrant one, offer to create a simple BM25 or TF-IDF search script in `tools/`. Keep it minimal — no vector embeddings, no external services.

## Synthetic Data & Finetuning (Advanced)

When the knowledge base matures, consider:
- **Synthetic Q&A pairs:** Generate question-answer pairs from wiki articles for downstream use
- **Finetuning datasets:** Format the wiki content into instruction-tuning format
- **Knowledge distillation:** Use the wiki to create condensed "cheat sheets" or study guides

These are **opt-in** operations — don't suggest them unless the user asks or the wiki has reached significant scale.

## Example Workflows

### Full session: New research topic

1. User pastes URLs or files → you save to `raw/`
2. User says "compile this" → you write articles + concepts + connections
3. User asks questions → you research, answer, and file results
4. User says "make slides" → you generate Marp presentation
5. User says "lint" → you find and fix gaps

### Quick add: Single article

1. User provides source
2. You summarize → write one article → update index → add backlinks
3. Done in one turn

### Incremental: Weekly review

1. User says "review what's new in my research"
2. You scan `raw/` for unprocessed sources
3. You lint `wiki/` for health
4. You suggest 2-3 new connections or articles
5. Execute on approved items

## Constraints

- **No vector embeddings / RAG** — the wiki structure (index + summaries + backlinks) is designed to be navigable by an LLM directly at this scale
- **Plain markdown only** — no binary formats, no special database
- **LLM writes, user curates** — the LLM is the author; the user reviews in Obsidian
- **Incremental by default** — avoid rewriting the entire wiki; update affected pages only
- **Provenance tracking** — every wiki article must link back to its raw source(s)
