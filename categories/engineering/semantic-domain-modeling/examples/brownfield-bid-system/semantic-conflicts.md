# Semantic Conflicts — Brownfield Bid System

> Mode: BROWNFIELD
> Status: VERIFIED_FOR_EXAMPLE

| ID | Concept / Fact | Conflict | Evidence A | Evidence B | Risk | Decision | Status |
|---|---|---|---|---|---|---|---|
| SC-001 | tender metadata authority | `project_documents` and legacy tender records can both appear usable | current project document flow | legacy resolver/fallback | HIGH | project_documents is target AUTHORITATIVE metadata; legacy record becomes HISTORICAL/compatibility | VERIFIED |
| SC-002 | TenderDocument vs ProjectDocument | generic document row may be mistaken for business tender authority | generic DB model | scoring requirement | HIGH | TenderDocument is a role/identity within project documents, not every project attachment | VERIFIED |
| SC-003 | parsed text identity | derived text can be treated as if it proves document identity | parser store | document requirement | MEDIUM | parsed text is DERIVED and must retain source identity | VERIFIED |
