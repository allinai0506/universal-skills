# 06 Context Projection：Ontology 不是 Prompt

## 核心做法

长期 Ontology 全量存仓库，Agent 只拿当前任务需要的一小片。

```text
Task
  -> Projection Resolver
  -> Authorized Ontology Slice
  -> Context Pack
  -> Agent
```

## Projection 文件应声明

- roles
- objects
- properties
- relations
- rules
- allowed_actions
- evidence policy
- exclusions

## 示例

“投标评分解析 Agent”不需要知道整个 CRM。

它只需要：

- TenderProject
- TenderDocument
- ScoringCriterion
- Section
- Project -> Document 关系
- extract_scoring_criteria 规则
- save_scoring_result 动作

## 原则

- 默认最小暴露。
- 权限过滤先于上下文编译。
- Action 是否可见与是否可执行必须分别校验。
- Projection 可以按 role / workflow / task 分层。
