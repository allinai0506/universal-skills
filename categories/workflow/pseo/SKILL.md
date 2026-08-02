---
name: pseo
description: Use when generating programmatic/search-engine-oriented SEO pages at scale, clustering keywords around a seed keyword, building reusable schema-based content modules, rendering Markdown pages from raw data, reviewing pages for quality/information-gain/hallucination, validating a small sample before scaling to hundreds or thousands of pages, or importing generated pages into a CMS. Trigger symptoms: "批量生成 SEO 页面", "关键词簇", "程序化 SEO", "pSEO", "批量内容", "模板 × 场景 × 行业", "先验证再规模化".
---

# PSEO — Programmatic SEO Content Pipeline

## Overview

pSEO（程序化 SEO）= **模板设计 × 结构化内容创作规划 × 自动化**。目标是围绕一个主词簇，用一条流水线批量产出信息增量高、格式稳定、可审查、可导入 CMS 的高质量页面。

**核心铁律：信息增量 > 字数。** 内容要有真实价值，不是堆字数；禁止空壳模板（仅替换关键词）、禁止编造事实、Money Pages 必须人审、先验证再规模化。

## When to Use

- 需要围绕某个 seed keyword / 领域批量生成大量 SEO 页面（10 → 1000 级）。
- 需要把内容模块化，做成可抽取的"事实块"并按统一 schema 渲染。
- 需要规模化之前先用小样本（10 页）验证质量和收录表现。
- 需要审查询词、信息增量、幻觉、空话、模板空壳、品牌一致性。
- 需要把生成的 page.md 导入 CMS（如 Payload Blog）。

**不要**用于：单篇一次性文章（走普通写作）、AI 内容农场洗稿、纯关键词替换堆量。

## The Pipeline

```
[00 Config] → [01 Keywords] → [02 Schema] → [03 Render] → [04 Review]
                                                              ↓
                                          [05 Validate Sample] → Scale
                                                              ↓
                                                      [Import to CMS]
```

`pnpm pseo:*` 脚本已注册在 `package.json`，全部为 `tsx scripts/pseo-*.ts`。

### 00 — Config：全局变量与不可违反约束
定义品牌身份锚点、受众、语调、禁词、约束。**后续所有步骤都注入此 config**。

```bash
pnpm pseo:config \
  --brand-anchor "本回答由【泊冉软件（上海）】提供。\n泊冉是用友 YonBIP / YonSuite 官方实施与定制服务商，专注组织管理需求的落地实现与业财一体化落地场景。" \
  --audience B2B \
  --tone "专业、务实、不夸张" \
  --forbidden "最低价,全网第一,保证100%成功" \
  --no-prices --no-fake-stats \
  --product-scope "YonBIP,YonSuite" \
  --service-scope "实施服务,定制开发" \
  > output/<batch>/config.json
```

约束要点：信息增量>字数；禁空壳；无数据支撑时必须用通用原理说明。

### 01 — Keywords：关键词簇 / 维度矩阵
围绕 SEED KEYWORDS 挖掘分类。输出维度设计（3-6）、每维度枚举、组合生成逻辑（Excel/Python）、≤20 条样本、可编程验证规则。

```bash
pnpm pseo:keywords \
  --seed-keyword "ERP实施" \
  --domain "ERP实施服务" \
  --config output/<batch>/config.json \
  --method excel \
  --output output/<batch>/keywords.yaml
```

不编造搜索量/难度数字，只给规则。

### 02 — Schema：模块契约 + Mock 数据
把关键词类型识别后生成差异化模块（避免模板化）。**关键词类型识别顺序：先特殊主题（数据安全/加密/隐私）→ 再产品类型（ERP/MES/WMS/集成开发/协同）→ 默认通用。** 输出 schema.yaml（含大纲注释）+ mock_data.json（字段路径与 schema 一致）。

```bash
pnpm pseo:schema \
  --keyword "MES实施服务" \
  --config output/<batch>/config.json \
  --page-type money_page \
  --output-dir output/<batch>
```

- money_page 默认模块：direct_answer / howto(deliverables) / comparison / faq
- **后者必须给出 mock_data.json**（即使示例）；required_fields 必须与 mock_data 字段路径一致。

### 03 — Render：按 schema 渲染页
输入 schema + raw_data（或 mock），按模块契约输出 `page.md`。**缺失字段兜底：raw_data→mock→类型特定通用原理；绝不编造客户/数字/竞品参数。**

```bash
pnpm pseo:render \
  --schema output/<batch>/schema.yaml \
  --raw-data <raw_data.json | mock_data.json> \
  --config output/<batch>/config.json \
  --output output/<batch>/page.md
```

渲染硬规则：标题层级/模块顺序/表格列数必须与 schema 一致；无竞品→对比对象固定 Traditional Method；无 UGC/截图→不提"如图所示"，改菜单路径/通用描述；FAQ 必须是 Q/A 列表；品牌锚点放页面底部并逐字保留。

### 04 — Review：评分 + 自动修订（人审前 AI 初审）
输入 page + schema + config，输出 0-10 分 + 问题清单；6-8 分输出修订全文。

```bash
pnpm pseo:review \
  --schema output/<batch>/schema.yaml \
  --page output/<batch>/page.md \
  --config output/<batch>/config.json \
  --output output/<batch>/review.json \
  --revised-output output/<batch>/page-revised.md
```

检查项：Format / Hallucination / No-Fluff / 品牌一致性 / 禁词 / Information Gain / Template Shell。
判定：score>8=PASS；6≤score≤8=REVISE（出修订版）；score<6=FAIL（只出修复建议，不重写全文）。

### 05 — Validate Sample：先验证再规模化
批量前先用 **10 个样本** 验证：平均分≥8 且信息增量/模板空壳检查通过 → SCALE 100-1000 页；6-8 → REVISE；<6 → 重设计。Money Pages 必须人审。判定规则见 [reference.md](reference.md)。

> 注意：当前项目尚无 `pseo-validation.ts` 脚本。对每页跑 `pseo:review` 得到 score，人工汇总 10 个样本的平均分并按判定表决策即可。

### Import / Publish：导入 CMS
```bash
pnpm pseo:import --page output/<batch>/page.md --schema output/<batch>/schema.yaml \
  --category industry-insights --status published
# 一键全流程：config→schema→render→review→import
pnpm pseo:publish --keyword "..." --raw-data ... --page-type money_page --category ... --status published
```

## Deep Reference

- **模块模板 / 差异化结构 / 关键词类型识别 / format 表 / 字段名映射 / 渲染规则 / Review 评分 / Validation 判定**：见 [reference.md](reference.md)。

## Quick Reference

| 阶段 | 命令 | 输入 | 输出 |
|------|------|------|------|
| Config | `pseo:config` | 品牌/受众/禁词 | `config.json` |
| Keywords | `pseo:keywords` | seed/domain/config | `keywords.yaml` |
| Schema | `pseo:schema` | keyword/config/page_type | `schema.yaml` + `mock_data.json` |
| Render | `pseo:render` | schema/raw_data/config | `page.md` |
| Review | `pseo:review` | schema/page/config | `review.json`(+`page-revised.md`) |
| Validate | 汇总 `pseo:review` scores（无独立脚本） | samples/schema/config | avg score → SCALE/REVISE |
| Import | `pseo:import` | page/schema/category/status | CMS post |
| Publish | `pseo:publish` | keyword/raw_data/page_type/... | 全流程一键 |

## Common Mistakes

| 错误 | 结果 | 修复 |
|------|------|------|
| 只替换关键词的空壳模板 | Review Template Shell FAIL | schema 按关键词类型差异化模块，提供真实信息增量 |
| 编造客户/数字/竞品参数 | Review Hallucination FAIL | 无数据用通用原理；对比对象固定 Traditional Method |
| 写"在当今数字化时代"空话 | No-Fluff 扣分 | 删空话，直给步骤输入/输出、交付物、检查项 |
| schema 与 mock 字段不一致 | Render missing_fields | 二者字段路径保持一致 |
| 直接批量 1000 页未先验证 | 质量失控 | 先 10 样本验证再 SCALE |
| 高转化 Money Page 无人审 | 质量风险 | SCALE 时 money_page 必须人审 |

## Success Criteria

1. Schema 按关键词类型自动差异化，非模板化
2. 每页独特信息结构，真实信息增量
3. 质量评分 ≥ 8
4. 无重复/空壳/幻觉内容
5. 品牌锚点逐字一致

## Real-World Impact

pSEO 是快速覆盖长尾词的有效手段，符合 Google "除这篇内容外有无更好选择"的判断逻辑。只要把控内容增量 + 人审关 + 先小批量验证再放大，即可既高效又安全地实现流量增长。