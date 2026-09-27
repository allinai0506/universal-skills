# Domain Model

> Status: DRAFT | VERIFIED | BLOCKED
> Scope: <bounded scope of this model>
> Last verified: <date / commit / evidence reference>

## 1. Glossary

| Canonical term | Code name | Definition | Not this | Aliases / forbidden names |
|---|---|---|---|---|
| <term> | `<Name>` | <meaning> | <non-examples> | <aliases> |

## 2. Objects

### <ObjectName>

- **Meaning:**
- **Identity:**
- **Lifecycle:**
- **Owner / bounded context:**
- **Authoritative source:**
- **Derived representations:**

## 3. Relationships

| Source | Relation | Target | Cardinality | Business meaning |
|---|---|---|---|---|
| <A> | <verb> | <B> | <1:N> | <meaning> |

## 4. States

### <ObjectName>

| State | Meaning | Allowed next states | Entry condition |
|---|---|---|---|
| <STATE> | <business guarantee> | <...> | <...> |

Forbidden transitions:

- `<STATE_A> -> <STATE_B>` because <reason>.

## 5. Actions

### <ActionName>

- **Actor:**
- **Target:**
- **Inputs:**
- **Preconditions:**
- **Permission:**
- **Changes:**
- **Side effects:**
- **Success result:**
- **Failure behavior:**

## 6. Invariants

1. <Invariant that must always remain true.>
2. <Invariant that must always remain true.>

## 7. Sources of Truth

| Fact | Classification | Authoritative source | Owner | Derived/cached copies | Conflict rule |
|---|---|---|---|---|---|
| <fact> | AUTHORITATIVE | <source> | <owner> | <copies> | <rule> |

## 8. Semantic Conflicts and Decisions

| Issue | Evidence | Decision | Status |
|---|---|---|---|
| <ambiguity> | <evidence> | <decision> | RESOLVED / UNVERIFIED / BLOCKED |

## 9. Evidence

| Evidence | Location | Claim | Confidence | Conflict? |
|---|---|---|---|---|
| <type> | <path/url/id> | <claim> | HIGH/MEDIUM/LOW | YES/NO |

## 10. Downstream Impact

- APIs affected:
- Storage affected:
- Workflows affected:
- Tests required:
- Agent actions affected:
