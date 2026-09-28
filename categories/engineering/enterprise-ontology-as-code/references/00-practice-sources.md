# 00 Practice Sources

本技能只借鉴公开工程做法，不复刻产品实现。

## TextQL 采用的实践

- Ontology 以文件形式存储在 Git-backed repository。
- 从数据库和文档逐步恢复业务语义。
- Agent 可以提出本体修改，但需要人工批准。
- 使用 validation / known-good queries 持续验证。
- Ontology 不只包含结构化数据语义，也逐步统一业务上下文。

参考：
- https://www.textql.com/blog/ontology-v3
- https://github.com/TextQLLabs/ontology-workshop-guide

## Palantir 采用的实践

- Object / Property / Link / Action 作为关键建模原语。
- 企业决策建模同时考虑 Data / Logic / Action / Security。
- Action 是一等公民，能够改变 Object / Property / Link 并产生副作用。
- Ontology 不只是语义层，还需要 Engine 与 Toolchain 支撑真实读写、权限和运行。

参考：
- https://www.palantir.com/docs/foundry/architecture-center/ontology-system
- https://www.palantir.com/docs/foundry/ontology/core-concepts/
