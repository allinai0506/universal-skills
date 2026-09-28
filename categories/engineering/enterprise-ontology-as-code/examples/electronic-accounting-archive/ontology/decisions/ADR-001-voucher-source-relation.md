# ADR-001：凭证与原始凭证关系建模为业务关系

## 背景
归档完整性依赖两者关系，关系不是单纯数据库 join。

## 决策
把 `voucher_has_source_document` 纳入 Ontology，并允许后续升级为携带匹配来源、置信度、确认人的关系对象。
