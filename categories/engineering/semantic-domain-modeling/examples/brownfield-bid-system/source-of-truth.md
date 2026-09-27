# Sources of Truth — Brownfield Bid System

> Mode: BROWNFIELD
> Status: VERIFIED_FOR_EXAMPLE

| Fact | AUTHORITATIVE | Other Representations | Write Owner | Conflict Rule | Evidence | Status |
|---|---|---|---|---|---|---|
| current tender metadata | project_documents | legacy tender record = HISTORICAL | document domain | current project metadata wins | intended + current flow | VERIFIED |
| tender binary | OBS object referenced by current metadata | local temp = CACHE | storage integration | OBS wins | storage flow | VERIFIED |
| parsed tender text | no independent authority; DERIVED from current binary | parser cache/results | parser service | regenerate from authoritative binary when invalid | parser flow | VERIFIED |
| scoring criterion | derived scoring record with source trace | UI projection | scoring domain | source trace must match current TenderDocument | requirement | VERIFIED |
