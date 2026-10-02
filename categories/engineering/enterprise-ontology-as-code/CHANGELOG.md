# Changelog

## v2.1.0 — Executable Knowledge & Ontology Impact Gate（2026-10-02）

- 保留原 Brownfield / Greenfield / Evolution / OEP / Runtime Projection。
- 新增 Executable Knowledge：生产代码为权威实现，Ontology 引用而不复制；UNKNOWN 不得静默转为正常业务结论。
- 新增 Phase 5.5 Ontology Impact Gate：`ontology_impact.py` 对 Git Diff 做确定性启发式检查。
- 新增 `.ontology-impact.yaml` 声明模板（`assets/templates/`）、`test_ontology_impact.py` 自动测试与 GitHub Actions 示例（`examples/ontology-impact-gate/`）。
- 新增 `references/10-executable-knowledge.md`、`references/11-ontology-impact-gate.md`。
- 从“文档约束”推进到“可进入 CI 的工程门禁”。

## v2.0.0 — Ontology-as-Code & Continuous Evolution

在原“语义对齐 / 本体发现”能力上新增：

- 标准 `ontology/` 仓库结构。
- Object / Relation / State / Rule / Action / Policy / Connector / Mapping / Projection 原语。
- Brownfield 首轮只读发现与 Evidence-first 机制。
- Action 运行时契约：授权、前置条件、幂等、事务、审计、失败与验证。
- Git / PR / OEP 持续演化流程。
- Golden Regression。
- Context Projection，避免把完整 Ontology 塞给 Agent。
- Validator / Index / Diff / Bootstrap 脚本。
- 电子会计档案与投标管理两个示例。
