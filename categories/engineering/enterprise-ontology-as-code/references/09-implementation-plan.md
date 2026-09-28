# 09 Implementation Plan：不要一次做完，按 5 个 PR 落地

## PR-1：Ontology Skeleton + Read-only Discovery

目标：只建立仓库资产，不改运行逻辑。

交付：

- `ontology/ontology.yaml`
- 1 个真实业务切片的 objects / relations / states / rules
- Evidence Inventory
- Semantic Conflict Report
- Validator 接入 CI

禁止：Action 真执行、自动写数据库、改业务流程。

验收：能回答“这个业务切片里有哪些对象、关系、状态、规则，它们的证据在哪”。

## PR-2：Source Mapping + Golden Tests

目标：把 Ontology 和真实实现对上。

交付：

- mappings/
- connectors/（只描述，不新增新服务）
- tests/golden/
- generated/index.json

验收：每个 active Object 可以追溯到真实事实源；关键规则至少有 Golden Case。

## PR-3：Action Contract + Policy

目标：把“系统能做什么”正式化。

交付：

- actions/
- policies/
- state transition guards
- action idempotency / transaction / audit / failure semantics

先绑定已有 service/API，不重写业务实现。

验收：任何写操作都能说明“谁、在什么条件下、调用什么、改变什么、失败怎么办”。

## PR-4：Runtime Projection

目标：让 Agent / Workflow 真正消费 Ontology。

交付：

- projections/
- Context Compiler / Resolver 最小适配
- 先权限过滤，再上下文编译
- Action 只通过已授权 contract 暴露

验收：一个真实 Agent 任务不再依赖手写大段业务 Prompt，而是从 Projection 获取业务定义。

## PR-5：Continuous Evolution

目标：建立持续演化闭环。

交付：

- OEP 模板与流程
- Agent 发现语义缺口后只生成 proposal
- Ontology Diff 检查
- Golden regression gate
- Human approval gate

验收：真实任务中出现新业务知识时，可以进入 PR，而不是只停留在 Agent 会话 Memory。
