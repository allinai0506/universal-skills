---
name: knowledge-capture
version: "2026.09.14-1"
synced-at: "2026-09-14T07:43:18"
description: >
  将 session 中的开发/改 bug/架构/需求确认结果按类型沉淀到 docs/。
  写 docs/ 不写 .wiki/，严格遵循现有格式，每条知识有明确归属。
---

# 知识沉淀工作流（knowledge-capture）

把每次 session 产生的隐性知识按类型沉淀到 `docs/` 下对应目录，让团队积累的工程记忆不散落在聊天记录里。

## 触发词

用户说出以下任一短语时触发本 skill：

- "沉淀一下" / "沉淀"
- "归档本次知识" / "归档 session 知识"
- "把刚才的结论记下来"
- "/沉淀" / "/knowledge-capture"
- "每周知识归档"

## ⚡ 30 秒决策：本次 session 值得沉淀吗？

在进入完整工作流之前，先用以下 3 个问题快速判定：

```
Q1: 本次 session 是否产生了可复用的知识？
    → 排查了 bug 根因？做了选型/拍板？踩了技术坑？确认了需求口径？
    → NO → 直接告知用户"本次未识别到值得沉淀的知识"，结束。

Q2: 这条知识是否已在现有文档中存在？
    → Grep 目标文件 → 已存在 → 跳过，不重复沉淀。

Q3: 这条知识是否有真实证据支撑？
    → 代码路径/PR 链接/对话片段/命令输出？
    → NO → 拒绝沉淀（禁止推测性知识）。
```

3 个 Q 全 YES 才进入正式工作流。

## 🚨 不可妥协的护栏

- 🚫 **只写 docs/，不写 .wiki/**：`docs/` 是人工维护的原始文档层；`.wiki/pages/` 是 `npm run wiki:ingest` 编译产物，skill 直接写会污染编译流程。
- 🚫 **禁止 Mock 知识**：每条知识必须有 session 中的真实证据。无证据不沉淀。
- ✅ **格式一致性**：写入前 MUST `Read` 一个同类现有文件作为格式参照，照葫芦画瓢。
- ✅ **原子写入**：一条知识一次 `Edit`/`Write`，失败不影响其他条目。
- ✅ **不重复沉淀**：写入前 `Grep` 目标文件，确认无重复主题。
- ✅ **知识与代码同 commit**：沉淀写入必须与本次代码变更同一个 commit 提交（`--amend` 或同 PR 内），禁止事后单独补提，保证知识与代码版本对齐。

## 目录分层

```
docs/          = 原始文档层（人工维护的 source of truth）
  ├─ lessons/       = session 经验沉淀（根因、教训、陷阱、集成经验、决策）← 本 skill 主战场
  ├─ references/    = 外部 SDK / 框架知识内部化（不归本 skill 管）
  ├─ specs/         = 产品需求规格、设计规范
  └─ exec-plans/    = 执行计划、技术债台账
.wiki/pages/   = 合成知识图谱（wiki:ingest 编译生成，skill 不碰）
```

## 知识类型路由表（速查）

> 完整路由细节（识别信号、写入锚点、模板）见 [`references/routing-table.md`](./references/routing-table.md)。

| # | 知识类型 | 识别信号 | 落点 | 写入方式 |
|---|---------|---------|------|---------|
| 1 | **Bug 根因分析** | 排查了 bug、定位零号病人、写了 diff | `docs/lessons/root-cause-analysis-<slug>.md` | `Write` 新建 |
| 2 | **通用工程教训/复盘** | 多问题归纳出规范、事故复盘 | `docs/lessons/lessons-learned.md` | `Edit` 追加 `## N.` 章节 |
| 3 | **技术陷阱（gotcha）** | 单点技术坑、bad/good 代码对比 | `docs/lessons/<tech>-gotchas.md` | `Edit` 追加（无则 `Write` 新建） |
| 4 | **架构/设计决策** | 选型、取舍、拍板了某方案 | `docs/lessons/decisions.md` | `Edit` 追加条目 |
| 5 | **技术债** | 遗留代码、mock 泄漏、文档失同步 | `docs/exec-plans/tech-debt-tracker.md` | `Edit` 追加到对应分类 |
| 6 | **产品需求确认** | 确认了需求口径、业务规则 | `docs/specs/<topic>.md` | `Write` 新建或 `Edit` 追加 |
| 7 | **外部集成经验** | 对接外部系统（CRM/OA/飞书）踩坑 | `docs/lessons/<system>-integration-lessons.md` | `Edit` 追加（无则 `Write` 新建） |

**落点选择逻辑**：
- 经验类（根因/教训/陷阱/集成/决策）→ `docs/lessons/`
- 结构化台账 → `docs/exec-plans/tech-debt-tracker.md`
- 产品需求 → `docs/specs/`

## 四步工作流

### 第 1 步：扫描 session → 输出候选清单

回顾本次对话，按路由表 7 类信号扫描：

- 🐛 bug 排查 / 🎯 决策拍板 / ⚠️ 踩坑 / 📋 需求澄清 / 🏗️ 架构确认 / 🗑️ 技术债 / 🔌 外部对接

输出候选清单（表格形式）：

```
| # | 知识摘要 | 类型 | 拟落点 | 新建/追加 |
|---|---------|------|--------|----------|
| 1 | 立项上传 bug：el-upload 缺 :disabled | Bug 根因分析 | docs/lessons/root-cause-analysis-initiation-upload.md | 新建 |
| 2 | CRM 匹配策略需 Feature Flag | 外部集成经验 | docs/lessons/crm-integration-lessons.md | 追加 |
```

判定不清的，归到"通用工程教训"或用 `AskUserQuestion` 让用户选类型。

**无候选时**：直接告知"本次 session 未识别到值得沉淀的知识"，结束。

### 第 2 步：用户确认

用 `AskUserQuestion`（`multiSelect: true`）让用户勾选要沉淀的条目：

- 用户可拒绝条目（不勾选）
- 用户可选 "Other" 编辑摘要或改类型
- 用户可全部拒绝

### 第 3 步：按格式写入

对每个确认条目，严格按顺序执行：

```
1. Grep 目标文件 → 确认无重复主题（有则跳过本条）
2. Read 格式参照文件（路由表"格式参照"列）
3. Read 模板文件（templates/<type>.md，若存在）
4. Read 目标文件（追加类必须，确定锚点；新建类跳过）
5. 填充内容：从 session 提取真实证据
6. 写入：
   - 追加类 → Edit 在正确锚点插入
   - 新建类 → Write 创建文件
```

**格式参照 fallback**：当 `templates/` 或 `references/` 不存在时，直接用 `docs/lessons/` 下现有同类文件作为格式参照（如 `root-cause-analysis-*.md`、`decisions.md`、`*-gotchas.md`）。

**工具速查**：

| 操作 | 工具 | 关键参数 |
|------|------|---------|
| 查重复 | `Grep` | `pattern`=主题关键词, `path`=目标文件 |
| 读参照 | `Read` | `file_path`=参照文件绝对路径 |
| 读目标 | `Read` | `file_path`=目标文件绝对路径 |
| 追加 | `Edit` | `old_string`=锚点文本, `new_string`=锚点+新内容 |
| 新建 | `Write` | `file_path`=新文件绝对路径, `content`=完整内容 |
| 确认 | `AskUserQuestion` | `multiSelect: true` |

写入后不再重复 `Read` 验证（`Edit`/`Write` 失败会报错）。

### 第 4 步：维护索引

| 动作 | 触发条件 | 工具 | 操作 |
|------|---------|------|------|
| 更新 lessons 索引 | 新建 `docs/lessons/` 文件 | `Edit` | 在 `docs/lessons/README.md` 文件清单表加一行 |
| 更新日期 | 追加到现有文件 | `Edit` | 更新文件头更新日期（若有） |
| 技术债 | 追加到 tracker | — | 无需额外索引（tracker 自身即索引） |

**不维护** `.wiki/pages/_index.md`——由 `npm run wiki:ingest` 编译生成。

## 门禁升格：同类问题出现 ≥2 次必须自动化

记一次是文档，出现第二次就是门禁缺失：

```
同类问题第几次出现？
    ├── 第 1 次 → 追加到 lessons-learned.md
    ├── 第 2 次 → 追加 + 立即写自动化门禁（单测、lint 规则或 pre-push 检查），
    │              并在对应章节"操作规范"注明"已固化到 XXX"
    └── 第 3 次 → 说明既有门禁未生效，先修门禁覆盖范围，再补章节
```

## 归档决策：教训何时退役

满足任一条件时，将对应章节移入 `docs/lessons/lessons-archive.md`：

- 对应模块已完全重构，教训不再适用；
- 已有全覆盖的自动化门禁，文字规范已冗余；
- 距最后一次引用超过 6 个月且无复发。

## slug 命名约定

- `docs/lessons/` 新建：`root-cause-analysis-<issue-id-小写>.md`、`<tech>-gotchas.md`、`<system>-integration-lessons.md`
- `docs/specs/` 新建：`<TOPIC>.md`（大写，参照 `DESIGN.md`）

## 何时拒绝沉淀

- ❌ 本次 session 只做了简单问答、查询、读代码，无沉淀价值
- ❌ `Grep` 命中——知识已在现有文档中存在
- ❌ 知识过于具体、不可复用（如"某次重启了服务"）
- ❌ 没有真实证据支撑的推测

## 自举

本 skill 的设计决策本身应作为第一条沉淀：落点到 `docs/lessons/decisions.md`，作为 dogfood 验证。