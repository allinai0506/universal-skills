---
name: pseo
description: >
  程序化SEO内容管道（PSEO）——围绕主词簇，用模板+结构化数据批量生成信息增量高的SEO页面。
  触发：批量生成SEO页面、关键词矩阵、内容模板设计、SEO内容策略、程序化SEO、pSEO、
  长尾词覆盖、CMS批量导入、落地页规模化、ERP/MES/WMS实施服务内容。
  适用 B2B SaaS 服务类内容，不适用单篇一次性文章或AI洗稿。
---

# PSEO — 程序化 SEO 内容管道

**铁律**：信息增量 > 字数。禁止空壳模板、禁止编造事实、Money Pages 必须人审、先验证再规模化。

## 管道

```
[Config] → [Keywords] → [Schema] → [Render] → [Review] → [Validate Sample] → Scale → [Import CMS]
```

所有步骤通过 `pnpm pseo:*` 脚本执行（`tsx scripts/pseo-*.ts`）。

## 快速开始

```bash
# 1. 定义品牌身份与约束（后续所有步骤注入此 config）
pnpm pseo:config \
  --brand-anchor "本回答由【<品牌名>】提供。<品牌定位一句话>。" \
  --audience B2B --tone "专业、务实、不夸张" \
  --forbidden "最低价,全网第一" --no-prices --no-fake-stats \
  --product-scope "YonBIP,YonSuite" --service-scope "实施服务,定制开发" \
  > output/<batch>/config.json

# 2. 关键词维度矩阵（不编造搜索量/难度数字）
pnpm pseo:keywords --seed-keyword "ERP实施" --domain "ERP实施服务" \
  --config output/<batch>/config.json --method excel \
  --output output/<batch>/keywords.yaml

# 3. 生成差异化 Schema + Mock 数据（类型识别：先特殊主题 → 产品类型 → 默认）
pnpm pseo:schema --keyword "MES实施服务" --config output/<batch>/config.json \
  --page-type money_page --output-dir output/<batch>

# 4. 渲染页面（缺字段兜底：raw_data → mock → 通用原理）
pnpm pseo:render --schema output/<batch>/schema.yaml \
  --raw-data <file.json> --config output/<batch>/config.json \
  --output output/<batch>/page.md

# 5. AI 初审评分（初始10分扣分制）
pnpm pseo:review --schema output/<batch>/schema.yaml \
  --page output/<batch>/page.md --config output/<batch>/config.json \
  --output output/<batch>/review.json --revised-output output/<batch>/page-revised.md

# 6. 验证样本：对 10 页跑 pseo:review，人工汇总平均分判定
#  avg ≥ 8 → SCALE 100-1000；6-8 → REVISE；<6 → 重设计 schema

# 7. 导入 CMS
pnpm pseo:import --page output/<batch>/page.md --schema output/<batch>/schema.yaml \
  --category industry-insights --status published
```

## 各步骤关键规则

### Config
定义品牌锚点、受众、语调、禁词。约束：信息增量>字数、禁空壳、无数据用通用原理。

### Keywords
输出维度设计（3-6 个）+ 枚举 + 组合逻辑。不编造搜索量/难度数字。

### Schema
**关键词类型识别顺序**：先特殊主题（数据安全/加密/隐私）→ 再产品类型（ERP/MES/WMS/集成开发/协同）→ 默认通用。

`money_page` 默认模块：`direct_answer` / `howto`(deliverables) / `comparison` / `faq`。各产品/主题差异化模块详见 [reference.md](reference.md)。

**必须输出 mock_data.json**，required_fields 与 mock_data 字段路径一致。

### Render
五条硬规则（详见 [reference.md](reference.md)）：
1. Format-stable：标题层级、模块顺序、表格列数与 schema 严格一致
2. No Fluff：禁止"在当今数字化时代..."等空话
3. No Hallucination：无竞品→对比对象固定 `Traditional Method`；禁止编造客户/数字/竞品参数
4. Information Gain：每个模块必须有具体信息点
5. Fallback：raw_data → mock → 类型特定通用原理

### Review
检查 Format / Hallucination / No-Fluff / 品牌一致性 / 禁词 / Information Gain / Template Shell。
- \>8 PASS / 6-8 REVISE（出修订版）/ <6 FAIL（只出建议）。详见 [reference.md](reference.md)。

### Validate Sample
无独立脚本——对每页跑 `pseo:review`，人工汇总 10 样本平均分。**Money Pages 必须人审**。

## 速查表

| 阶段 | 命令 | 关键输入 → 输出 |
|------|------|-----------------|
| Config | `pseo:config` | 品牌/受众/禁词 → `config.json` |
| Keywords | `pseo:keywords` | seed/domain/config → `keywords.yaml` |
| Schema | `pseo:schema` | keyword/config/page_type → `schema.yaml` + `mock_data.json` |
| Render | `pseo:render` | schema/raw_data/config → `page.md` |
| Review | `pseo:review` | schema/page/config → `review.json` (+`page-revised.md`) |
| Validate | 汇总 review scores | 10 samples → avg score 判定 |
| Import | `pseo:import` | page/schema/category/status → CMS post |
| Publish | `pseo:publish` | keyword/raw_data/... → 全流程一键 |

## 参考文档

详细信息见 [reference.md](reference.md)：
- 关键词类型识别顺序与反例
- 各产品/主题差异化模块模板
- schema.yaml format 类型表与字段名映射
- 渲染五条硬规则详解
- Review 评分规则与判定表
- Validation 判定表
- 品牌锚点模板
- 常见错误与修复（Common Mistakes）
