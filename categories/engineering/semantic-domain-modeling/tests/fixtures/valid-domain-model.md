# Domain Model

> Status: VERIFIED
> Scope: tender scoring
> Last verified: test fixture

## Glossary

Tender Document is the official procurement document, not a bid response or generic project attachment.

## Objects

### BidProject
Stable project identity and lifecycle owner.

### TenderDocument
Official tender material used as evidence for scoring extraction.

## Relationships

BidProject has one active TenderDocument. TenderDocument contains ScoringCriterion evidence.

## States

TenderDocument: UPLOADED -> PARSED -> VERIFIED. VERIFIED -> UPLOADED is forbidden.

## Actions

VerifyTenderDocument requires parsed text and marks the business evidence usable.

## Invariants

1. Every scoring criterion must be traceable to tender source text.
2. A project has at most one active tender document.

## Sources of Truth

Tender metadata is AUTHORITATIVE in `project_documents`; binary content is authoritative in object storage. Parsed text is DERIVED.

## Semantic Conflicts and Decisions

TenderFile is deprecated as a business term; use TenderDocument. Status: RESOLVED.
