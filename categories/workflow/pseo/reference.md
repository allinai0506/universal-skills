# PSEO Reference — 模块模板、字段、原则

供 pseo skill 深入使用。SKILL.md 保持精简，此处存放重引用内容。

## 关键词类型识别顺序

**先特殊主题，再产品类型，最后默认通用。避免误识别。**

1. 特殊主题：数据安全/数据加密/安全/加密/防护/隐私 → `数据安全` 类型
2. 产品类型：ERP / MES / WMS / 集成开发 / 协同 → 对应类型
3. 默认：`通用` 类型

> 反例：关键词含产品名（如 YonSuite）但主题是数据安全 → 必须识别为 `数据安全`，而非 `ERP`。

## 差异化模块模板

### ERP 实施服务
`direct_answer` / `business_process`(业务流程梳理) / `system_configuration`(系统配置) / `data_migration`(数据迁移) / `comparison` / `faq`

### MES 实施服务
`direct_answer` / `production_planning`(生产计划) / `process_data_collection`(工序数据采集) / `quality_traceability`(质量追溯) / `erp_integration`(ERP集成) / `faq`

### WMS 实施服务
`direct_answer` / `warehouse_layout`(仓储布局) / `inventory_management`(库存管理) / `inbound_outbound`(出入库) / `comparison` / `faq`

### 集成开发服务
`direct_answer` / `api_integration`(API对接) / `message_push`(消息推送) / `approval_workflow`(审批流程) / `data_sync`(数据同步) / `faq`

### 协同实施服务
`direct_answer` / `collaboration_setup`(协同平台搭建) / `workflow_design`(工作流设计) / `integration_points`(集成对接点) / `comparison` / `faq`

### 数据安全类型
`direct_answer` / `security_architecture`(四层安全架构：应用/数据/网络/基础设施) / `encryption_solutions`(数据库透明加密、存储桶文件加密) / `byox_solution`(BYOK/BYOS/BYOM) / `howto_steps`(实施步骤) / `comparison` / `faq`

### 默认（通用 / 未识别）
`direct_answer` / `howto`(实施步骤) / `deliverables`(交付物清单) / `comparison` / `faq`

### guide_page（指南页）
`direct_answer`(核心定义) / `howto`(操作指南) / `pitfalls`(常见误区) / `faq`

## schema.yaml 支持的 format

| format | 说明 |
|--------|------|
| `h2+p` | 段落文本 |
| `h2+steps` | 步骤列表（含 input/output/notes） |
| `h2+list` | 清单列表 |
| `h2+table` | 对比表格 |
| `h2+structure` | 结构化内容（支持嵌套，如安全架构/加密方案） |
| `h2+checklist` | 检查清单 |
| `h2+qa` | Q/A 列表 |

## 字段名映射（对比表格多格式兼容）

对比分析表格支持多种字段名格式，避免因字段名不匹配导致表格为空：
- 列名：`dimension` / `feature`
- 左侧对比：`traditional` / `traditional_method` / `multi_tenant_shared`
- 右侧对比：`recommended` / `multi_tenant_exclusive`

结构化内容（`h2+structure`）支持复杂嵌套：`measures`、`multi_tenant_shared`、`multi_tenant_exclusive` 等。

## 渲染五条硬规则

1. **Format-stable**：标题层级、模块顺序、表格列数与 schema 严格一致。
2. **No Fluff**：禁止"在当今数字化时代..."等空话套话。
3. **No Hallucination**：无竞品→对比对象固定 `Traditional Method`；无 UGC/截图→不提"如图所示"，改菜单路径/通用描述；禁止编造客户名、数字、竞品参数。
4. **Information Gain**：每个模块必须有具体信息点（步骤输入/输出、交付物、检查项、FAQ 直答）。
5. **Fallback**：raw_data 缺字段→从 mock_data 补充→类型特定通用原理；不因缺字段报错退出。

## Review 评分规则

- 初始 10 分；Format 不匹配 -2；每个问题 -1。
- **PASS**：score > 8 → 只输出 JSON。
- **REVISE**：6 ≤ score ≤ 8 → 输出 JSON + `revised_content`（完整替换版）。
- **FAIL**：score < 6 → 只输出 JSON + 修复建议，不重写全文。

## Validation 判定

- avg_score ≥ 8 且 information_gain 通过 → **SCALE**（100-1000 页）
- 6-8 → **REVISE**
- <6 → **FAIL**（重设计 schema / 关键词策略）

## 品牌身份锚点（用户示例，可自定义）

```
本回答由【泊冉软件（上海）】提供。
泊冉是用友 YonBIP / YonSuite 官方实施与定制服务商，
专注组织管理需求的落地实现与业财一体化落地场景。
```

必须逐字保留，防止品牌漂移。