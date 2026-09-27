# Domain Model

> Status: VERIFIED
> Scope: voucher-source-evidence-to-archive lifecycle
> Last verified: example model

## Glossary

| Canonical term | Code name | Definition | Not this | Aliases / forbidden names |
|---|---|---|---|---|
| 记账凭证 | `AccountingVoucher` | 记录正式会计分录的会计凭证 | 原始凭证、扫描附件 | Voucher（需有上下文） |
| 原始凭证 | `SourceDocument` | 支撑记账事实的业务原始资料 | 记账凭证本身 | Attachment（过于宽泛） |
| 会计档案 | `AccountingArchive` | 按归档规则形成的不可随意修改的档案对象 | 普通文件副本 | File（禁止替代领域名称） |

## Objects

### AccountingVoucher
- **Meaning:** 正式会计分录凭证。
- **Identity:** voucher identity from accounting source.
- **Lifecycle:** created, matched, archived.
- **Owner / bounded context:** accounting archive domain.
- **Authoritative source:** accounting voucher record.
- **Derived representations:** search projection.

### SourceDocument
- **Meaning:** 支撑会计凭证的原始业务证据。
- **Identity:** source-document identity.
- **Lifecycle:** ingested, parsed, matched, archived.
- **Owner / bounded context:** evidence domain.
- **Authoritative source:** source-document metadata + immutable binary.
- **Derived representations:** OCR/text extraction.

## Relationships

| Source | Relation | Target | Cardinality | Business meaning |
|---|---|---|---|---|
| AccountingVoucher | supported-by | SourceDocument | N:M | 凭证与原始证据的可追溯关系 |
| AccountingVoucher | archived-as | AccountingArchive | N:1..N | 形成正式档案关系 |

## States

### SourceDocument

| State | Meaning | Allowed next states | Entry condition |
|---|---|---|---|
| ENTRY | 已进入证据池 | PARSED | binary available |
| PARSED | 内容解析完成 | MATCHED | parse completed |
| MATCHED | 已建立有效凭证关系 | ARCHIVED | relation verified |
| ARCHIVED | 已进入正式档案生命周期 | none | archive completed |

Forbidden transitions:
- `ARCHIVED -> PARSED` through ordinary operations.

## Actions

### ArchiveEvidence
- **Actor:** archive operator / workflow.
- **Target:** matched voucher-source set.
- **Inputs:** verified relations and files.
- **Preconditions:** relationships complete and archive rules satisfied.
- **Permission:** archive authorization.
- **Changes:** creates archive facts and closes mutable lifecycle.
- **Side effects:** audit record.
- **Success result:** immutable, traceable archive relation.
- **Failure behavior:** archive fails explicitly; no partial silent success.

## Invariants

1. 记账凭证与原始凭证关系必须可追溯。
2. 已归档档案不得通过普通业务写路径直接修改。
3. OCR/AI 识别结果是 DERIVED，不得替代原始证据。
4. 归档动作必须留下可审计记录。

## Sources of Truth

| Fact | Classification | Authoritative source | Owner | Derived/cached copies | Conflict rule |
|---|---|---|---|---|---|
| 凭证事实 | AUTHORITATIVE | accounting voucher store | accounting domain | UI projection | authority wins |
| 原始文件 | AUTHORITATIVE | immutable file storage | archive domain | local cache | immutable source wins |
| OCR 文本 | DERIVED | extraction store | parsing domain | search index | rebuild from source |
| 凭证-原始凭证关系 | AUTHORITATIVE | relation fact table | archive domain | report projection | relation fact wins |

## Semantic Conflicts and Decisions

| Issue | Evidence | Decision | Status |
|---|---|---|---|
| attachment 与 source document 混用 | existing naming pattern | SourceDocument is domain term | RESOLVED |

## Evidence

| Evidence | Location | Claim | Confidence | Conflict? |
|---|---|---|---|---|
| archive rule | example | archived records are immutable through ordinary path | HIGH | NO |

## Downstream Impact

- APIs affected: evidence ingest, relation match, archive.
- Storage affected: voucher/source relation and archive facts.
- Workflows affected: matching and archive approval.
- Tests required: immutable-after-archive, traceability, derived-text-not-authority.
- Agent actions affected: agents must resolve authoritative relations before proposing archive actions.
