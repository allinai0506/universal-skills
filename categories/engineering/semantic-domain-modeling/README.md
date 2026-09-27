# semantic-domain-modeling v1.1.0

A complete Agent Skill package for **semantic-first software development**.

It creates a Minimum Viable Ontology so humans and AI agents share the same business model, and it now supports both new repositories and mature running repositories.

## Execution modes

### Greenfield

Define semantics before implementation.

```text
Requirements → Domain Model → Validation Gate → Handoff → Coding
```

### Brownfield

Reconstruct existing semantics before changing them.

```text
Repository Archaeology
→ Evidence Inventory
→ Semantic Inventory
→ Intended / Implemented / Observed
→ As-Is
→ To-Be
→ Source of Truth
→ Migration Plan
→ Gate
→ Semantic Convergence
```

The first Brownfield pass is **READ_ONLY** for business code and business data structures.

## Package layout

```text
semantic-domain-modeling/
├── SKILL.md
├── README.md
├── VALIDATION.md
├── CHANGELOG.md
├── references/
│   ├── modeling-protocol.md
│   ├── semantic-conflicts.md
│   ├── source-of-truth.md
│   ├── state-actions-invariants.md
│   ├── brownfield-archaeology.md
│   ├── semantic-migration.md
│   ├── multi-agent-alignment.md
│   └── agents-md-integration.md
├── scripts/
│   ├── init_domain_model.py
│   └── validate_domain_model.py
├── assets/
│   ├── domain-model.template.md
│   ├── brownfield-domain-model.template.md
│   ├── semantic-conflicts.template.md
│   ├── source-of-truth.template.md
│   ├── semantic-migration-plan.template.md
│   ├── semantic-handoff.template.md
│   └── semantic-review-checklist.md
├── tests/
│   ├── test_validate_domain_model.py
│   └── fixtures/
└── examples/
    ├── bid-system/
    ├── electronic-accounting-archive/
    └── brownfield-bid-system/
```

## Install

Copy the **whole directory**. Do not copy `SKILL.md` alone.

Common locations:

```text
~/.agents/skills/semantic-domain-modeling/
~/.codex/skills/semantic-domain-modeling/
~/.claude/skills/semantic-domain-modeling/
```

## Initialize — Greenfield

```bash
python scripts/init_domain_model.py /path/to/repo --mode greenfield
```

Creates:

```text
docs/domain-model.md
```

## Initialize — Brownfield

```bash
python scripts/init_domain_model.py /path/to/repo --mode brownfield
```

Creates, without overwriting existing work:

```text
docs/domain-model.md
docs/semantic-conflicts.md
docs/source-of-truth.md
docs/semantic-migration-plan.md
```

## Validate — Greenfield

```bash
python scripts/validate_domain_model.py /path/to/repo/docs/domain-model.md --mode greenfield
```

## Validate — Brownfield bundle

```bash
python scripts/validate_domain_model.py /path/to/repo/docs/domain-model.md --mode brownfield --bundle
```

## Use with an Agent

For a new repository:

```text
Use the semantic-domain-modeling skill in Greenfield Mode for this repository.
Do not enter coding until the semantic gate passes.
```

For an existing repository:

```text
Use the semantic-domain-modeling skill in Brownfield Mode for this repository.
The first pass must remain READ_ONLY for business code and business data structures.
Produce the required semantic artifacts and stop at the Brownfield Discovery Gate.
```

No long supplemental prompt should be required. The skill owns the protocol.

## Principle

> Code implements the domain model. Code does not define the domain model by itself.

> For mature repositories: reconstruct reality before normalizing it.
