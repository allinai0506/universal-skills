# Domain Model — Brownfield Bid System Example

> Mode: BROWNFIELD
> Status: VERIFIED_FOR_EXAMPLE
> Discovery Rule: READ_ONLY during semantic archaeology. This example documents findings; it does not authorize code changes.

## Scope

Tender-document identity, scoring-criteria parsing, and the data path used by scoring analysis in an already-running bid-management repository.

## Evidence Inventory

| Evidence | Location | Layer | What it claims | Confidence | Conflict? |
|---|---|---|---|---|---|
| product requirement | docs/scoring.md | Intended | scoring criteria must trace to the active tender document | HIGH | no |
| project document table | DB/project_documents | Implemented | project-linked document metadata is stored here | HIGH | yes |
| legacy tender record | DB/tender_document | Implemented | older services may still read tender metadata here | HIGH | yes |
| object storage | OBS | Implemented | binary PDF bytes are stored outside DB | HIGH | no |
| production warning | runtime logs | Observed | some scoring flows fail to resolve tender text and fall back | HIGH | yes |
| parser tests | tests/scoreparse | Implemented | parser accepts resolved text, not arbitrary project files | MEDIUM | no |

## Semantic Inventory

| Name | Location | Classification | Meaning / Hypothesis | Status |
|---|---|---|---|---|
| TenderDocument | domain language | CANONICAL_CANDIDATE | the active tender document used as bidding authority | VERIFIED |
| ProjectDocument | DB/service | TECHNICAL_REPRESENTATION | generic project-linked document metadata | VERIFIED |
| TenderFile | legacy service | LEGACY_ALIAS | historical naming for tender-document file representation | VERIFIED |
| OBS object | storage | TECHNICAL_REPRESENTATION | binary payload of a document | VERIFIED |
| ParsedTenderText | parser | TECHNICAL_REPRESENTATION | derived searchable text from the tender document | VERIFIED |

## Intended Model

A BidProject has one current active TenderDocument for scoring work. ScoringCriterion values are derived from that TenderDocument and every criterion must remain traceable to the source text. Storage records and parsed text are technical representations, not separate business tender documents.

## Implemented Model

Metadata can be encountered in both `project_documents` and a legacy `tender_document` path. Binary content resides in object storage. Parsed text is separately persisted. Some service code contains fallback logic that can read historical records when the primary resolution path fails.

## Observed Behavior

Runtime evidence shows that the primary scoring path can fail to resolve current tender text while the binary conversion service itself succeeds. Historical fallback can then mask the identity/source mismatch, causing a request to continue with a non-primary path rather than exposing the semantic conflict.

## As-Is Model

### Glossary

| Canonical Candidate | Code Name(s) | Current Meaning | Not This | Aliases / Conflicts | Status |
|---|---|---|---|---|---|
| Tender Document | TenderDocument, TenderFile | business tender authority plus several technical forms | generic project attachment | TenderFile is legacy alias | VERIFIED |
| Project Document | ProjectDocument | generic metadata link between project and uploaded content | automatically the tender authority | may wrap TenderDocument metadata | VERIFIED |
| Parsed Tender Text | ParsedTenderText | text derived from tender binary | original document | must never become authority for document identity | VERIFIED |

### Objects

| Object | Identity | Current Representations | Owner | Lifecycle | Current Authority | Status |
|---|---|---|---|---|---|---|
| BidProject | project id | project row/API model | project domain | active/closed | project store | VERIFIED |
| TenderDocument | logical document id + project association | project_documents, legacy record, OBS binary, parsed text | document domain | uploaded/parsed/verified | ambiguous before convergence | UNVERIFIED |
| ScoringCriterion | criterion id + source location | parsed result rows | scoring domain | extracted/verified | derived from TenderDocument | VERIFIED |

### Relationships

| Source | Relation | Target | Current Evidence | Status |
|---|---|---|---|---|
| BidProject | has-current | TenderDocument | requirements + project link data | VERIFIED |
| TenderDocument | produces | ParsedTenderText | parser/storage implementation | VERIFIED |
| TenderDocument | contains-source-for | ScoringCriterion | requirement + parser tests | VERIFIED |

### States

| Object | State | Meaning | Legal From | Legal To | Evidence | Status |
|---|---|---|---|---|---|---|
| TenderDocument | UPLOADED | binary and metadata exist | none | PARSED | upload flow | VERIFIED |
| TenderDocument | PARSED | text extraction completed | UPLOADED | VERIFIED | parser flow | VERIFIED |
| TenderDocument | VERIFIED | document/text are accepted for scoring | PARSED | VERIFIED | business rule | VERIFIED |

### Actions

| Action | Actor | Target | Preconditions | Change | Side Effects | Evidence | Status |
|---|---|---|---|---|---|---|---|
| UploadTenderDocument | user | TenderDocument | project exists | creates metadata/binary | storage write | upload flow | VERIFIED |
| ParseTenderDocument | system | TenderDocument | binary accessible | creates parsed text | parser call | parser flow | VERIFIED |
| ExtractScoringCriteria | system | TenderDocument | verified text available | creates derived criteria | scoring rows | scoring flow | VERIFIED |

### Invariants

- A scoring run must resolve the current TenderDocument before extracting criteria.
- Every ScoringCriterion must be traceable to the exact source document/text location.
- A derived parsed-text record must not redefine which TenderDocument is current.
- Historical fallback must not silently override the current document authority.

### Sources of Truth

| Fact | Current Candidate | Classification | Conflict Rule | Evidence | Status |
|---|---|---|---|---|---|
| project identity | project store | AUTHORITATIVE | project store wins | schema/service | VERIFIED |
| tender metadata | project_documents vs legacy tender record | UNKNOWN | BLOCKED until target decision | code/schema | UNVERIFIED |
| tender binary bytes | OBS object | AUTHORITATIVE | storage object keyed by authoritative metadata | storage integration | VERIFIED |
| parsed tender text | parsed text store | DERIVED | regenerate from authoritative binary when invalid | parser flow | VERIFIED |

## To-Be Model

### Glossary

| Canonical Term | Code Name | Meaning | Forbidden / Legacy Aliases |
|---|---|---|---|
| Tender Document | TenderDocument | current authoritative tender document for a BidProject | TenderFile as new naming |
| Project Document | ProjectDocument | generic project-linked document metadata | treating every ProjectDocument as TenderDocument |
| Parsed Tender Text | ParsedTenderText | derived text representation | treating parsed text as document identity |

### Objects

| Object | Identity | Owner | Lifecycle | AUTHORITATIVE Source |
|---|---|---|---|---|
| BidProject | project id | project domain | active/closed | project store |
| TenderDocument | authoritative project-document id | document domain | UPLOADED/PARSED/VERIFIED | project_documents metadata + OBS binary |
| ScoringCriterion | criterion id | scoring domain | extracted/verified | derived scoring store, traceable to TenderDocument |

### Relationships

| Source | Relation | Target | Cardinality / Rule |
|---|---|---|---|
| BidProject | has-current | TenderDocument | exactly one current document for scoring |
| TenderDocument | produces | ParsedTenderText | zero/one current derived text representation |
| TenderDocument | contains-source-for | ScoringCriterion | every criterion references source location |

### States

| Object | State | Meaning | Legal From | Legal To |
|---|---|---|---|---|
| TenderDocument | UPLOADED | authoritative metadata/binary exist | none | PARSED |
| TenderDocument | PARSED | current binary text extraction succeeded | UPLOADED | VERIFIED |
| TenderDocument | VERIFIED | accepted for downstream scoring | PARSED | VERIFIED |

### Actions

| Action | Actor | Target | Preconditions | Result / State Change | Permission |
|---|---|---|---|---|---|
| UploadTenderDocument | user | TenderDocument | project writable | creates current document | project document write |
| ParseTenderDocument | system | TenderDocument | authoritative binary accessible | UPLOADED → PARSED | parser service |
| VerifyTenderDocument | authorized user/system | TenderDocument | parsed output consistent | PARSED → VERIFIED | verification policy |
| ExtractScoringCriteria | system | TenderDocument | state VERIFIED | creates traceable derived criteria | scoring service |

### Invariants

- Exactly one current TenderDocument is eligible for scoring per BidProject.
- All scoring criteria are derived from and traceable to that current TenderDocument.
- Legacy records are HISTORICAL/compatibility data and cannot override current authority.
- Failure to resolve current authority is explicit; it is not hidden by historical fallback.

### Sources of Truth

| Fact | AUTHORITATIVE Source | Other Representations | Conflict Rule |
|---|---|---|---|
| current tender metadata | project_documents | legacy tender record as HISTORICAL | authoritative metadata wins |
| binary content | OBS referenced by current metadata | local temp file as CACHE | OBS wins |
| parsed text | parsed-text store as DERIVED | in-memory parse as transient | regenerate from authoritative binary |
| scoring criteria | scoring result store as DERIVED | UI projections | criteria must point to source document/location |

## Semantic Conflicts

See `semantic-conflicts.md`. The material conflict is whether legacy tender metadata can still behave as authority. The To-Be decision classifies it as HISTORICAL/compatibility only.

## Migration Direction

See `semantic-migration-plan.md`. Migration is incremental: first freeze new semantics, instrument legacy reads, move reads/writes to authoritative metadata, then remove fallback after evidence shows no required callers remain.

## Discovery Gate

- [x] Evidence inventory complete for current example scope
- [x] Semantic inventory complete for current example scope
- [x] Intended / Implemented / Observed separated
- [x] Material conflicts recorded
- [x] As-Is model grounded
- [x] To-Be model defined
- [x] Critical target sources of truth defined
- [x] Migration plan created
- [x] Business code unchanged during discovery
