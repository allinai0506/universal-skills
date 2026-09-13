# 知识类型路由表（detail）

> 每类知识一节，含：识别信号 / 落点路径 / 格式参照 / 写入锚点 / 索引维护 / 格式模板。
> 与 `SKILL.md` 的路由表互补：那张表是速查，本文件是执行手册。

## 落点选择总原则

```
经验类知识（根因、教训、陷阱、集成经验、决策）→ docs/lessons/
结构化台账（技术债）                          → docs/exec-plans/tech-debt-tracker.md
产品需求规格                                  → docs/specs/
```

**绝不写 `.wiki/pages/`**——那是 `npm run wiki:ingest` 编译产物，由编译流程维护。

---

## 类型 1：Bug 根因分析

### 识别信号
- 排查了具体 bug，定位到"零号病人"（第一行错误代码）
- 写了修复 diff
- 设计了防复发测试
- session 中出现"为什么...不生效""根因""剥洋葱"等关键词

### 落点
```
docs/lessons/root-cause-analysis-<issue-id-小写或-slug>.md
```
- 有 issue 编号：`root-cause-analysis-ijssgg.md`
- 无 issue 编号：`root-cause-analysis-<feature-bug-简述>.md`，如 `root-cause-analysis-initiation-upload.md`

### 格式参照
`docs/lessons/` 下现有根因分析文件；若无，参照 `.wiki/pages/root-cause-analysis-ijssgg.md` 的结构（剥洋葱法），但写入时去掉 wiki frontmatter。

### 模板
`templates/root-cause.md`

### 写入方式
**新建文件**。Write 工具创建。

### 写入前检查
- Grep `docs/lessons/` 确认无同名/同主题文件

### 索引维护
- 在 `docs/lessons/README.md` 目录结构表加一行

---

## 类型 2：通用工程教训/复盘

### 识别信号
- 多个问题归纳出一条规范或操作守则
- 事故复盘、回滚总结
- 流程改进（如"今后 PR 必须带测试证据"）
- session 中出现"以后应该""规范""教训""复盘"等关键词

### 落点
```
docs/lessons/lessons-learned.md
```
追加新章节，**不新建文件**。

### 格式参照
`docs/lessons/lessons-learned.md` 现有章节；若无，参照 `.wiki/pages/lessons-learned.md` 的章节结构（问题背景/经验教训表/操作规范/验证命令）。

### 模板
`templates/lessons-section.md`

### 写入方式
**追加**。Edit 工具，在文件末尾的最后一个 `---` 分隔符之后追加新章节。

### 写入锚点
- 读 `lessons-learned.md`，找到最后一个 `## N.` 章节结束位置
- 在其后追加 `\n---\n\n## N+1. <新章节标题>`

### 写入前检查
- Grep `lessons-learned.md` 确认无同主题章节

### 索引维护
- 无需（lessons-learned 已在 README 目录结构表中）

---

## 类型 3：技术陷阱（gotcha）

### 识别信号
- 单点技术坑，有 bad/good 代码对比
- 框架盲区、API 误用、配置陷阱
- session 中出现"原来...要这样写""踩坑""陷阱""以为...其实"等关键词
- 不涉及完整 bug 排查链路（那是根因分析），只是一条经验

### 落点
```
docs/lessons/<tech>-gotchas.md
```
- 已有同技术文件 → 追加 `## N.` 章节
- 无同技术文件 → 新建文件（文件头写一句简介，再追加章节）

### 格式参照
`docs/references/vue-gotchas.md`（结构参照：问题/正确写法/调试方法），但写入 `docs/lessons/`。

### 模板
`templates/gotcha.md`

### 写入方式
- **追加**：Edit 工具，在文件末尾追加 `## N. <陷阱标题>`
- **新建**：Write 工具，文件头一行 `# <Tech> 陷阱与调试经验` + 一句简介，再写第一章

### 写入锚点（追加类）
- 读目标文件，找到最后一个 `## N.` 章节
- 在其后追加新章节

### 写入前检查
- Glob `docs/lessons/*gotchas*` 确认是否已有同技术文件
- Grep 目标文件确认无同主题章节

### 索引维护
- 新建文件时在 `docs/lessons/README.md` 目录结构表加一行

---

## 类型 4：架构/设计决策

### 识别信号
- 选型决策（A vs B，拍板选 A）
- 取舍权衡（性能 vs 可维护性）
- 否决了某个备选方案并说明理由
- session 中出现"决定用""选型""权衡""为什么不选"等关键词

### 落点
```
docs/lessons/decisions.md
```
追加决策条目，**不新建文件**（所有决策汇总在一个文件，便于回溯）。

### 格式参照
`docs/lessons/decisions.md` 现有条目；若无，参照 `.wiki/pages/` 中 decision 类页面的结构（背景/决策/备选方案表/权衡/影响范围）。

### 模板
`templates/decision-log.md`

### 写入方式
**追加**。Edit 工具，在文件末尾追加新决策条目，用 `---` 分隔。

### 写入锚点
- 读 `decisions.md`，在文件末尾追加 `\n---\n\n## N. <决策标题>`

### 写入前检查
- Grep `decisions.md` 确认无同主题条目

### 索引维护
- 无需（decisions 已在 README 目录结构表中）

---

## 类型 5：技术债

### 识别信号
- 发现遗留代码、废弃目录未清理
- mock 泄漏、测试缺口
- 文档与代码失同步
- session 中出现"遗留""应该清理""技术债""欠的"等关键词

### 落点
```
docs/exec-plans/tech-debt-tracker.md
```
追加记录到对应分类，**不新建文件**。

### 格式参照
`docs/exec-plans/tech-debt-tracker.md` 现有记录

### 模板
`templates/tech-debt.md`

### 写入方式
**追加**。Edit 工具，按 `type` 归类，追加到对应分类下。

### 字段规范
```yaml
- area: <模块/包/文件>
  type: <god-class | dead-code | mock-leak | out-of-sync-doc | dependency-debt | test-gap>
  severity: <high | medium | low>
  status: open          # 新登记的一律 open
  source: <发现来源，如 "session 2026-06-18 排查 XX 时发现">
  note: <一句话说明与建议处理方式>
```

### 写入锚点
- 读 `tech-debt-tracker.md`
- 按 `type` 找到对应分类（遗留清理类 / 文档同步类 / 待登记）
- 追加到该分类最后一条记录之后
- 若无合适分类，追加到 `### 待登记` 下

### 写入前检查
- Grep `tech-debt-tracker.md` 确认无同 area 记录

### 索引维护
- 无需额外索引（tracker 自身即索引）

---

## 类型 6：产品需求确认

### 识别信号
- 和用户确认了业务规则、口径、边界
- 明确了"这个功能到底要做什么"
- session 中出现"确认一下""业务上是""需求是""口径"等关键词

### 落点
```
docs/specs/<TOPIC>.md
```
- 已有同 topic spec → Edit 追加段落
- 无 → Write 新建（参照现有 specs 格式）

### 格式参照
`docs/specs/` 下现有同类文档（如 `DESIGN.md`、`UAT_PLAN.md`）

### 写入方式
- **追加**：Edit 工具，在对应章节追加
- **新建**：Write 工具，文件名大写（参照 `DESIGN.md`、`WIKI.md`）

### 写入前检查
- Glob `docs/specs/*.md` 确认是否已有同 topic 文件

### 索引维护
- 新建 spec：在 `docs/specs/` 的 README（若有）登记；无 README 则跳过

---

## 类型 7：外部集成经验

### 识别信号
- 对接外部系统（CRM、OA、飞书、招标平台）踩坑
- 字段映射、时区契约、错误码处理
- session 中出现"CRM 返回""OA 接口""飞书回调""对接"等关键词

### 落点
```
docs/lessons/<system>-integration-lessons.md
```
- 已有同系统文件 → 追加 `## N.` 章节
- 无 → 新建文件（参照 `docs/references/crm-integration-lessons.md` 头部格式）

### 格式参照
`docs/references/crm-integration-lessons.md`（结构参照：来源/适用范围/编号章节/相关文档），但写入 `docs/lessons/`。

### 模板
`templates/gotcha.md`（结构相近：编号章节 + 要点列表）

### 写入方式
- **追加**：Edit 工具，在文件末尾追加 `## N. <经验标题>`
- **新建**：Write 工具，文件头：
  ```
  # <系统> 对接经验教训

  > 来源：<日期 + 事故/场景描述>
  > 适用范围：<哪些集成场景适用>
  ```

### 写入锚点（追加类）
- 读目标文件，找到最后一个 `## N.` 章节
- 在其后追加新章节
- 更新文件底部"相关文档"链接（若新章节引用了其他文档）

### 写入前检查
- Glob `docs/lessons/*integration-lessons*` 确认是否已有同系统文件
- Grep 目标文件确认无同主题章节

### 索引维护
- 新建文件时在 `docs/lessons/README.md` 目录结构表加一行

---

## 路由决策树

当难以判定类型时，按此顺序判断：

```
有 bug 排查 + diff 修复？
  → 类型 1 Bug 根因分析

是对外部系统的对接经验？
  → 类型 7 外部集成经验

是单点技术坑（bad/good 对比）？
  → 类型 3 技术陷阱

发现了遗留代码/失同步？
  → 类型 5 技术债

是选型/取舍/拍板？
  → 类型 4 架构/设计决策

是业务规则/需求口径确认？
  → 类型 6 产品需求确认

是多个问题归纳出的规范/复盘？
  → 类型 2 通用工程教训
```
