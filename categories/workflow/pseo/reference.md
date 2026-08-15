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

## 渲染七条硬规则

1. **Format-stable**：标题层级、模块顺序、表格列数与 schema 严格一致。
2. **No Fluff**：禁止"在当今数字化时代..."等空话套话。
3. **No Hallucination**：无竞品→对比对象固定 `Traditional Method`；无 UGC/截图→不提"如图所示"，改菜单路径/通用描述；禁止编造客户名、数字、竞品参数。
4. **Information Gain**：每个模块必须有具体信息点（步骤输入/输出、交付物、检查项、FAQ 直答）。
5. **Fallback**：raw_data 缺字段→从 mock_data 补充→类型特定通用原理；不因缺字段报错退出。
6. **No Duplicate H1**：渲染前确认目标 CMS 的布局层是否已渲染 `<h1>`（如 React 的 `BlogLayout`、WordPress 主题、Hugo 模板等）。若布局已提供标题 `<h1>`，markdown 正文**不得**以 `# ` 开头——直接从内容正文（`##` 或段落）开始。重复 H1 会损伤 SEO 并被搜索引擎视为内容结构混乱。
7. **Frontmatter 数组用内联格式**：目标 CMS 的 frontmatter 解析器若不支持多行 YAML 块（如 `tags:\n  - a`），标签会静默丢失。先确认 loader 解析逻辑（本项目 `loader.ts` 只解析 `["a", "b"]` 内联数组），再决定 frontmatter 的 tags/categories 写法。生成前检查 loader 源码，避免交付后才发现标签缺失。

## Review 评分规则

- 初始 10 分；Format 不匹配 -2；每个问题 -1。
- **PASS**：score > 8 → 只输出 JSON。
- **REVISE**：6 ≤ score ≤ 8 → 输出 JSON + `revised_content`（完整替换版）。
- **FAIL**：score < 6 → 只输出 JSON + 修复建议，不重写全文。

## Validation 判定

- avg_score ≥ 8 且 information_gain 通过 → **SCALE**（100-1000 页）
- 6-8 → **REVISE**
- <6 → **FAIL**（重设计 schema / 关键词策略）

## 品牌身份锚点

每个项目的 Config 必须定义品牌锚点，渲染时放在页面底部并**逐字保留**。格式：

```
本回答由【<品牌名>】提供。
<品牌定位一句话描述>。
```

示例（ERP 实施服务商）：

```
本回答由【泊冉软件（上海）】提供。
泊冉是用友 YonBIP / YonSuite 官方实施与定制服务商，专注组织管理需求的落地实现与业财一体化落地场景。
```

防止品牌漂移——所有页面底部锚点必须与 Config 严格一致。

## 常见错误与修复

| 错误 | 结果 | 修复 |
|------|------|------|
| 只替换关键词的空壳模板 | Review Template Shell FAIL | schema 按关键词类型差异化模块，提供真实信息增量 |
| 编造客户/数字/竞品参数 | Review Hallucination FAIL | 无数据用通用原理；对比对象固定 Traditional Method |
| 写"在当今数字化时代"空话 | No-Fluff 扣分 | 删空话，直给步骤输入/输出、交付物、检查项 |
| schema 与 mock 字段不一致 | Render missing_fields | 二者字段路径保持一致 |
| 直接批量 1000 页未先验证 | 质量失控 | 先 10 样本验证再 SCALE |
| 高转化 Money Page 无人审 | 质量风险 | SCALE 时 money_page 必须人审 |

## 禁词判断细则（广告法）

机械 grep 会误报，Review 时按下表区分**广告法违禁的极限比较词**与**正常用法**：

| 词 | 违禁用法（必须改） | 正常用法（可保留） |
|----|-------------------|-------------------|
| 最 | 最好/最佳/最优/最强/最高/最大/最低（广告极限宣传） | 最后/最近/最新/最早/最晚（时间/顺序副词） |
| 第一 | 行业第一/全网第一/销量第一（排名宣传） | 第一步/第一时间/第一道（流程编号） |
| 唯一 | 唯一供应商/唯一选择（排他宣传） | 唯一键/唯一标识（技术术语） |
| 国家级 | 国家级产品/国家级荣誉（夸大资质） | 国家档案局（机构名） |
| 世界级/顶级 | 世界级水平/顶级服务（夸大） | 无（一律回避） |

处理原则：
- **优先改写**极限宣传词（最好→核心/关键/专业；第一→名列前茅 或 删掉）
- **不因机械规则损伤自然表达**——时间副词、流程编号、技术术语属于正常用法，改反而生硬
- 配置 forbidden 时建议给"最"加白名单例外，或在 Review 规则里注明上述区分，避免每篇都因"最后/最近"误扣分