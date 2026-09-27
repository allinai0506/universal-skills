# Domain Model

> Status: VERIFIED
> Scope: bid project tender-document and scoring-criteria flow
> Last verified: example model

## Glossary

| Canonical term | Code name | Definition | Not this | Aliases / forbidden names |
|---|---|---|---|---|
| 投标项目 | `BidProject` | 一次正式投标活动的业务主体 | 普通销售项目 | project（过于宽泛） |
| 招标文件 | `TenderDocument` | 招标方发布并作为投标与评分依据的正式文件 | 投标文件、任意项目附件、解析文本 | TenderFile（旧称） |
| 评分项 | `ScoringCriterion` | 可追溯到招标文件原文的正式评分规则 | AI 猜测、摘要 | ScoreItem（需逐步废弃） |

## Objects

### BidProject
- **Meaning:** 一次投标活动。
- **Identity:** project id。
- **Lifecycle:** initiation to closed.
- **Owner / bounded context:** bid domain.
- **Authoritative source:** project record.
- **Derived representations:** search/read projections.

### TenderDocument
- **Meaning:** 当前有效招标文件业务对象。
- **Identity:** document id plus active relation to BidProject.
- **Lifecycle:** uploaded, parsed, verified.
- **Owner / bounded context:** bid document domain.
- **Authoritative source:** `project_documents` metadata + object storage binary.
- **Derived representations:** extracted text, AI parse result.

## Relationships

| Source | Relation | Target | Cardinality | Business meaning |
|---|---|---|---|---|
| BidProject | has-active | TenderDocument | 1:0..1 | 项目当前用于投标分析的唯一有效招标文件 |
| TenderDocument | contains-evidence-for | ScoringCriterion | 1:N | 每一评分项必须可回溯原文 |

## States

### TenderDocument

| State | Meaning | Allowed next states | Entry condition |
|---|---|---|---|
| UPLOADED | 文件已成为项目当前文件 | PARSED | binary available |
| PARSED | 技术解析完成但未代表业务正确 | VERIFIED | parsed text exists |
| VERIFIED | 可作为评分解析业务输入 | none | verification passed |

Forbidden transitions:
- `VERIFIED -> PARSED` through ordinary business actions.

## Actions

### ExtractScoringCriteria
- **Actor:** scoring service / authorized agent.
- **Target:** verified TenderDocument.
- **Inputs:** authoritative document identity and parsed text.
- **Preconditions:** active document exists and is VERIFIED.
- **Permission:** scoring workflow.
- **Changes:** creates/updates derived scoring criteria.
- **Side effects:** evidence links are stored.
- **Success result:** criteria are traceable.
- **Failure behavior:** explicit failure; do not silently use historical tender files.

## Invariants

1. 一个投标项目最多只有一个当前有效招标文件。
2. AI 评分解析只能读取当前有效招标文件。
3. 每个评分项必须可追溯到招标文件原文位置。
4. 历史文件不得作为静默 fallback 掩盖当前数据错误。

## Sources of Truth

| Fact | Classification | Authoritative source | Owner | Derived/cached copies | Conflict rule |
|---|---|---|---|---|---|
| 当前招标文件元数据 | AUTHORITATIVE | `project_documents` | bid domain | DTO/search index | authority wins |
| 招标文件二进制 | AUTHORITATIVE | object storage | document domain | local temp | object storage wins |
| 解析正文 | DERIVED | parser output store | document domain | cache | rebuild from binary |
| 评分项 | DERIVED | scoring result store | scoring domain | UI projection | must retain evidence |

## Semantic Conflicts and Decisions

| Issue | Evidence | Decision | Status |
|---|---|---|---|
| TenderFile vs TenderDocument | code aliases | TenderDocument is canonical | RESOLVED |

## Evidence

| Evidence | Location | Claim | Confidence | Conflict? |
|---|---|---|---|---|
| business rule | example | one active tender file | HIGH | NO |

## Downstream Impact

- APIs affected: tender resolve, scoring parse.
- Storage affected: project document metadata and parsed content.
- Workflows affected: scoring extraction.
- Tests required: no-active-document, historical-fallback rejection, evidence traceability.
- Agent actions affected: scoring agent must resolve the authoritative TenderDocument first.
