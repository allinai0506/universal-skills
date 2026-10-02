---
name: enterprise-ontology-as-code
version: "2026.09.28-1"
synced-at: "2026-09-28T12:46:30"
description: Build and continuously evolve a versioned, validated, executable ontology/ asset layer for enterprise software. Use for greenfield bootstrap on new repos, READ_ONLY brownfield discovery on existing repos, cross-system capabilities needing objects/relations/states/actions/policies contracts, fixing semantic drift across frontend/backend/database, establishing a shared semantic layer for multi-agent systems with context projections, or proposing evidence-based ontology evolution (OEP) with diff, golden tests and human review.
---

# Enterprise Ontology-as-Code & Continuous Evolution

## 1. 技能目标

把企业软件中的业务概念、关系、状态、规则、动作、权限、工作流、系统映射与运行时上下文，从分散在数据库、代码、接口、文档和人的经验中的隐式知识，转换为仓库内可版本化、可验证、可评审、可执行的 `ontology/` 资产。

本技能不是“写一份术语表”，也不是“画一张知识图谱”。最终交付必须能进入工程流程：

`发现 -> 建模 -> 映射 -> 动作约束 -> 权限约束 -> 测试 -> PR -> 运行时投影 -> 持续演化`

## 2. 适用场景

- 新仓库：开发前统一业务语义与运行规则。
- 已运行仓库：从现有代码、数据库、API、页面、测试和文档中反向恢复真实业务模型。
- Agent / Workflow 系统：建立稳定的企业语义层，让不同 Agent 读取同一套业务定义。
- 修复长期语义漂移：同一术语在前端、后端、数据库、流程中含义不一致。
- 新增跨系统业务能力：需要明确对象、状态、动作、权限及写回边界。
- 重大 Bug 复盘：发现缺陷根因来自隐式业务规则或状态约束缺失时，将规则沉淀进 Ontology。

## 3. 强制工作模式

### A. BROWNFIELD_DISCOVERY（存量仓库）

第一轮必须 `READ_ONLY`。禁止修改业务代码、数据库脚本或生产配置。

必须先完成：

1. Repository Archaeology（仓库考古）
2. Semantic Inventory（语义清单）
3. Evidence Map（证据映射）
4. Conflict Report（冲突报告）
5. Candidate Ontology（候选本体）

只有在候选本体通过评审后，才能进入落地修改。

### B. GREENFIELD_BOOTSTRAP（新仓库）

不得试图一次定义整个企业。只围绕第一个真实业务闭环建模，例如：

`客户 -> 报价 -> 审批 -> 合同`

或：

`记账凭证 -> 原始凭证匹配 -> 完整性检查 -> 归档`

### C. EVOLUTION（持续演化）

禁止 Agent 直接静默修改正式 Ontology。所有语义变化必须：

`发现差异 -> 生成 OEP -> 证据 -> Diff -> 测试 -> Human Review -> Merge`

OEP = Ontology Evolution Proposal（本体演化提案）。

## 4. 目标仓库标准目录

执行本技能后，目标仓库应逐步形成：

```text
ontology/
├── ontology.yaml
├── objects/
├── relations/
├── states/
├── rules/
├── actions/
├── policies/
├── workflows/
├── connectors/
├── mappings/
├── projections/
├── tests/
│   └── golden/
├── decisions/
├── proposals/
└── generated/
```

说明：

- `objects/`：业务对象及属性。
- `relations/`：业务对象之间的有意义关系。
- `states/`：状态机及允许转换。
- `rules/`：可独立验证的业务规则。
- `actions/`：改变企业状态的动作契约。
- `policies/`：谁在什么条件下可以读取或执行。
- `workflows/`：多动作编排，不等于传统审批流。
- `connectors/`：外部系统能力声明。
- `mappings/`：Ontology 与 DB/API/Event/File 的事实映射。
- `projections/`：针对 Agent、工作流、页面的上下文投影。
- `tests/golden/`：已知输入与已知正确结果。
- `decisions/`：为什么这样建模。
- `proposals/`：待评审的语义演化提案。
- `generated/`：只允许脚本生成，禁止人工编辑。

## 5. 核心建模原语

必须至少支持以下原语：

### Object（业务对象）
表示真实业务实体或事件。ID 一经激活不可随意修改。

必须包含：

- `id`
- `name`
- `description`
- `lifecycle`
- `identity`
- `properties`
- `evidence`

### Relation（关系）
只建模具有业务语义的问题，不把所有数据库外键都升级为关系。

必须回答：

- 起点对象是谁？
- 终点对象是谁？
- 业务含义是什么？
- 基数是什么？
- 关系本身是否携带业务属性？若携带，应升级为 Object-backed Relation。

### State（状态）
必须明确：

- 合法状态集合
- 初始状态
- 终态
- 允许转换
- 禁止转换
- 转换触发者

### Rule（规则）
一个规则只回答一个可判定问题。禁止把整段流程埋在一个 Rule 中。

### Action（动作）
Action 是一等公民，不只是 Tool 描述。

每个 Action 必须包含：

- `target`
- `inputs`
- `preconditions`
- `authorization`
- `effects`
- `side_effects`
- `idempotency`
- `transaction`
- `audit`
- `failure_behavior`
- `bindings`

任何写操作若无法描述上述字段，不允许进入正式 Ontology。

### Policy（权限策略）
至少约束：

- 读取哪些对象/属性
- 可执行哪些 Action
- 条件型限制
- 是否允许 Agent 继承用户权限
- 是否允许服务账号独立执行

### Connector / Mapping（连接器 / 映射）
Ontology 不得假装自己是事实源。必须记录真实来源：

- 数据库表与字段
- API
- 事件
- 文件
- 计算逻辑
- 外部系统

### Projection（运行时投影）
长期 Ontology 与单次 Agent Context 必须分离。

Projection 定义当前任务允许暴露的：

- 对象
- 属性
- 关系
- 规则
- 动作
- 权限
- 证据

Agent 不应直接获得完整 Ontology。

## 6. 执行流程

### Phase 0 — Scope Lock

先写出：

- Goal
- Non-goals
- First business slice
- Systems in scope
- Read/write boundaries
- Acceptance tests

不得使用“梳理整个企业”“统一所有业务概念”作为范围。

### Phase 1 — Evidence-first Discovery

按优先级收集证据：

1. 真实运行代码与测试
2. 数据库 Schema / Migration
3. API 契约 / Event Schema
4. 状态机 / 枚举 / 常量
5. 生产运行日志与真实案例
6. 产品文档 / 需求文档
7. UI 文案
8. README / 注释

遇到冲突时，不得自行决定业务真相。记录：

- `intended`：文档宣称的语义
- `implemented`：代码实际执行的语义
- `observed`：运行证据体现的语义

### Phase 2 — Semantic Inventory

产出清单：

- Objects
- Terms / Aliases
- Relations
- States
- Rules
- Actions
- Roles / Policies
- Workflows
- External systems
- Conflicts
- Unknowns

每一个正式项必须有 Evidence Ref。

### Phase 3 — Candidate Ontology

只建立当前业务闭环所需最小模型。

建模顺序固定：

`Object -> Relation -> State -> Rule -> Action -> Policy -> Mapping -> Projection`

不要先从数据库表自动一比一生成 Object。

### Phase 4 — Runtime Binding

对每个 Active Action，必须明确：

- 调用哪个服务 / API / command
- 谁负责事务
- 是否幂等
- 超时策略
- 重试策略
- 失败后是否补偿
- 是否写审计事件
- 执行后的状态如何重新读取确认

如果 Action 只有自然语言描述而没有 binding，状态必须保持 `experimental`。

### Phase 5 — Tests

最少执行 6 类检查：

1. Schema validation
2. Reference integrity
3. State transition validation
4. Action contract validation
5. Policy coverage
6. Golden regression

涉及高风险写操作时，增加：

- 幂等测试
- 重放测试
- 重试测试
- 事务边界测试
- 权限绕过测试
- 并发冲突测试

### Phase 5.5 — Ontology Impact Gate

持续开发仓库不要求每个任务修改 Ontology，但可能影响业务语义的 Git Diff 必须经过 `ontology_impact.py`。

`Git Diff -> ontology_impact.py -> ontology_validate.py -> PR Review`

命中风险但无 Ontology 变化时，必须提供 `.ontology-impact.yaml` 的 `impact: none + reason + evidence`，否则 REVIEW_REQUIRED。Gate 防遗漏，不替代 Human Review。详见 `references/11-ontology-impact-gate.md`。

### Phase 6 — PR Gate

PR 必须包含：

- 为什么改 Ontology
- 哪些业务定义变化
- Evidence
- Before / After
- 是否 Breaking Change
- 影响的 Object / Relation / Action / Policy / Projection
- Golden Tests 结果
- Migration / Compatibility Plan

禁止在普通业务 PR 中悄悄重定义核心业务术语。

### Phase 7 — Runtime Projection

对 Agent / Workflow 生成最小上下文包，而不是把全部 ontology 文件塞进 Prompt。

执行前：

`Task -> Projection -> Authorized Ontology Slice -> Context Pack`

执行后：

`Observation -> Evidence -> Finding -> Proposed Ontology Patch`

不得自动 Merge。

### Phase 8 — Continuous Evolution

当真实任务暴露新知识时：

1. 记录 Observation
2. 判断是否是一次性事实还是长期业务知识
3. 若为长期知识，生成 OEP
4. 引用证据
5. 提供 Ontology Diff
6. 补 Golden Case
7. 执行验证
8. 人工批准
9. Merge
10. 更新版本与索引

## 7. 生命周期与版本规则

统一生命周期：

- `experimental`：候选或尚未完成运行时绑定。
- `active`：已验证并可被运行时依赖。
- `deprecated`：仍兼容，但禁止新依赖。

ID 规则：

- `id` 是稳定机器标识。
- `name` 是显示名称，可以调整。
- 已 active 的 `id` 禁止仅因中文名称变化而重命名。

版本规则：

- PATCH：描述、别名、非语义元数据修正。
- MINOR：新增兼容对象、属性、关系、动作、规则。
- MAJOR：删除/重命名 active ID、改变基数、收紧或放宽关键权限、改变 Action effects、破坏状态转换兼容性。

## 8. Brownfield 特殊规则

### 8.1 首轮禁止“按理想业务重写现实”

必须保留三层：

- Intended
- Implemented
- Observed

### 8.2 冲突不直接修

先生成 `decisions/` 或 `proposals/`。

### 8.3 数据库不是唯一真相

数据库只能证明存储结构，不能单独证明业务语义。

### 8.4 前端枚举不是状态机

必须沿调用链追到实际持久化和状态转换代码。

### 8.5 同名不等于同义

例如：`归档状态`、`流程状态`、`匹配状态` 不得因为都叫 `status` 就合并。

## 9. Agent 行为边界

Agent 必须：

- 引用证据再建模。
- 明确推断与事实。
- 优先最小可用 Ontology。
- 产生 Diff，而不是重写整套本体。
- 对 Breaking Change 提醒并停止自动落地。
- 对 Action / Policy 变化默认要求人工评审。
- 在验证通过前不得宣称完成。

Agent 禁止：

- 仅凭表名自动生成正式对象。
- 把所有外键都升级成业务关系。
- 让 Agent 自己扩大权限。
- 让 Action 绕过原系统的业务校验。
- 把 Prompt 中的业务规则当作最终事实源。
- 修改 generated 文件作为源定义。
- 自动批准自己的 Ontology 提案。

## 10. Definition of Done

一个业务切片只有同时满足以下条件才算完成：

- [ ] 核心 Object 有稳定 ID 与证据。
- [ ] 关键 Relation 明确业务语义与基数。
- [ ] 状态机明确合法转换。
- [ ] 决策规则独立建模。
- [ ] 写操作全部通过 Action 契约暴露。
- [ ] Action 有授权、幂等、事务、审计、失败语义。
- [ ] Active Action 有真实 binding。
- [ ] 数据源与系统映射存在。
- [ ] 至少一个 Projection 可供真实 Agent/Workflow 使用。
- [ ] Golden Case 覆盖主路径和关键异常路径。
- [ ] 验证脚本通过。
- [ ] 语义变化经过 PR / Human Review。

## 11. 标准交付物

每次执行必须输出：

1. `Ontology Scope`
2. `Evidence Inventory`
3. `Semantic Conflicts`
4. `Ontology Diff`
5. `Runtime Bindings`
6. `Golden Tests`
7. `Breaking Changes`
8. `Open Questions`
9. `Recommended Next Slice`
10. `Validation Result`

## 12. 推荐命令

将本技能包中的脚本复制或适配到目标仓库后：

```bash
python scripts/ontology_validate.py ontology
python scripts/ontology_index.py ontology
python scripts/ontology_diff.py <base-ref> <head-ref> ontology
python scripts/ontology_impact.py <base-ref> <head-ref> ontology
```

验证未通过时，不得进入 Merge。
