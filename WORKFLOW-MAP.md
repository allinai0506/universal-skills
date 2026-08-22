# WORKFLOW-MAP · 统一开发生命周期映射

> 目标：把 speckit / gstack / ohmyclaude(omc) / pstack(poteto) / superpowers / matt pocock 六套范式的精华，
> 编排到**一条统一生命周期**上。统一的是骨架（阶段 + 门禁），不统一的是肌肉（各技能实现）。
>
> 本文档是未来 router 元技能的数据基础。生成于 2026-08-22，基于 SKILLS-INDEX.md（236 技能）+ 核心流程技能精读。
>
> **Canonical（首选）选取标准**：平台中立、描述与参考文档最完整、能与相邻阶段技能自然衔接。
> 备选保留不删除，仅在特定条件下替换首选。

---

## 一、生命周期总览

```
S0 准备 → S1 意图 → S2 规格 → S3 规划 → S4 实现 → S5 验证 → S6 审查 → S7 交付 → S8 沉淀
 worktree  为什么做   做什么    怎么做    动手做    证明对    挑毛病    上上线    变聪明

横切关注点（任何阶段可介入）：
  🔍 调试诊断   🧠 上下文管理   📐 工程原则约束（pstack principle-*）
```

**门禁规则**（借鉴各范式之长）：
- S1→S2：意图不清不得写规格（speckit clarify 精神）
- S3→S4：无书面计划不动代码，除非走「微改动」快速路径（writing-plans 精神）
- S4→S5：声明完成前必须跑真实验证并出示证据（verification-before-completion / prove-it-works 精神）
- S5→S6→S7：已上线系统的 PR 必须过生产风险审计（production-risk-review）

---

## 二、分阶段映射表

### S0 会话准备与环境隔离

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `using-git-worktrees` | 动手前确保隔离工作区，superpowers 链的入口习惯 |
| 备选 | `project-session-manager` | 多工单/多 worktree 并行场景升级替代 |
| 备选 | `recall` | 接续之前的工作时先重建上下文 |
| 辅助 | `deepinit` | 新代码库首次进入时生成分层 AGENTS.md |

### S1 意图澄清（为什么做）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `brainstorming` | 创造性工作前探索意图/需求/设计，微改动可跳过本阶段 |
| 备选 | `grill-with-docs` | 需要同步产出 ADR 与领域词汇表时 |
| 备选 | `deep-interview` | 需求歧义极大、需要苏格拉底式追问时 |
| 输入适配 | `parse-prd` / `product-analysis` | 输入是飞书 PRD 或需要竞品/优先级分析时 |

### S2 规格定义（做什么）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `speckit-specify` + `speckit-clarify` | 最严谨：章程支撑 + 定向澄清；大型特性必用 |
| 备选 | `to-spec` | 中型任务轻量路线：对话直接综合成规格并入 tracker |
| 备选 | `gstack-spec` | 产出物直接是 issue/ticket、要与 GitHub 流衔接时 |
| 配套 | `speckit-constitution` | 项目级章程，一次配置长期复用 |
| 配套 | `domain-modeling` | 有领域建模诉求时沉淀统一语言 |

### S3 方案规划（怎么做）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `writing-plans` | 动代码前写实现计划，bite-sized 步骤 + 预埋验证点 |
| 架构先行 | `architect`（pstack） | 先勾勒类型签名与模块结构再填实现 |
| 大型加码 | `speckit-plan` + `speckit-tasks` | 文档流水线式计划 + 有序任务清单 |
| 计划评审 | `gstack-plan-eng-review` / `plan-ceo-review` / `plan-design-review` | 仅大型/高风险特性启用多视角会审 |
| 一致性检查 | `speckit-analyze` / `speckit-checklist` | 规格-计划-任务交叉校验 |
| 原型探路 | `prototype` / `arena` / `principle-exhaust-the-design-space` | 无先例的交互或设计决策，先对比再定案 |

### S4 实现执行（动手做）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical（方法论）** | `coding/test-driven-development` | RED→GREEN→REFACTOR 主循环，附 writing-good-tests.md |
| canonical（编排） | `subagent-driven-development` | 有子代理能力时的默认执行引擎（executing-plans 自述优先推荐它） |
| 备选（编排） | `executing-plans` | 无子代理环境下的顺序执行 + 检查点 |
| 并行加速 | `dispatching-parallel-agents` / `swarm` / `team` / `ultrawork` | 任务相互独立时才并行，共享状态禁止 |
| 直改路线 | `implement`（matt pocock） | 已有规格/ticket 的中小型实现 |
| 无人值守 | `autopilot` / `ralph` / `figure-it-out` | 夜间/长任务自治模式，需配 show-me-your-work 决策日志 |
| TDD 去重 | ~~`tdd-workflow`~~ `engineering/tdd` `pstack/tdd` | 见「五、冗余去重清单」 |

### S5 验证测试（证明对）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `verification-before-completion` | 完成声明前必须跑命令、看输出、留证据 |
| 原则兜底 | `principle-prove-it-works` | 对真实产物验证，拒绝"编译通过就算完" |
| 测试专项 | `e2e-testing` / `self-verifying-tests` / `cpp-testing` / `eval-harness` | 按层按语言选用 |
| 循环验证 | `ultraqa` | 测试-修复-再测直至目标达成 |
| 项目级 | `create-verification-skill` + `maintain-verification-skill` | 把"这个项目怎么验"固化成技能 |

### S6 审查质检（挑毛病）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `code-review`（engineering） | 规范轴 + spec 轴双线并行审查 |
| 对抗审查 | `interrogate` / `cog-4d-audit` | CI 全绿但仍不放心的隐藏缺陷挖掘 |
| 生产风险 | `production-risk-review` | **已上线系统 PR 必过**，替代普通 review |
| 安全 | `security-review` / `gstack-cso` | 清单式安全审查 / OWASP+威胁建模 |
| 影响面 | `blast-radius` | 改动前评估可能破坏什么 |
| QA | `gstack-qa`（改）/ `gstack-qa-only`（只报不改） | 真机浏览器 QA |
| AI 痕迹清理 | `ai-slop-cleaner` / `receiving-code-review` | 清理 AI slop；被审时不盲从反馈 |

### S7 交付集成（上上线）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `finishing-a-development-branch` → `gstack-ship` | 分支集成决策 → 合基线、测试、版本、PR 一条龙 |
| 发布工程 | `ai-release-engineer` / `release` | AI 代码合并前的验证门禁 / 仓库规则驱动发布 |
| 部署专项 | `deployment/*`（docker/migrations/deployment-patterns）、项目专属如 `xiyu-server-deploy` | 按项目选用 |
| 上线后 | `gstack-canary` | 金丝雀监控与回滚决策 |

### S8 沉淀学习（变聪明）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `knowledge-capture` | 按 docs/ 现有格式沉淀开发知识，归属明确 |
| 自动提炼 | `continuous-learning-v2` | 会话观察 → 本能 → 技能演化（v2 优先于 v1） |
| 回顾复盘 | `gstack-retro` | 周期性工程回顾 |
| 元技能 | `learner` / `reflect` / `automate-me` | 把成功流程固化为新技能 |

---

## 三、横切关注点

### 🔍 调试诊断（升级路径）

```
systematic-debugging（canonical 入口）
  └─ 升级 root-cause-hunter（逆向追踪证明根因）
       └─ 升级 paranoid-debugging（生产关键代码的证据级再验证）
其他工具：diagnosing-bugs（HITL 循环）/ trace（竞争假设）/ deep-dive / gstack-investigate
```

### 🧠 上下文管理

`principle-guard-the-context-window`（批量路由给子代理）+ `strategic-compact`（节点压缩）+
`context-save/context-restore`（跨会话续接）。

### 📐 原则约束层

pstack 的 21 条 `principle-*` 不属于任何阶段，是**所有阶段共享的约束**（如 subtract-before-you-add、fix-root-causes、sequence-verifiable-units）。Router 引导时作为全局 system prompt 级提示注入。

---

## 四、任务规模路由表

| 任务类型 | 判定特征 | 路径 |
|---|---|---|
| 微改动 | 单文件、<50 行、行为明确 | S4 直改 → S5 验证（跳过 S0-S3） |
| Bug 修复 | 有复现路径 | S0 → 调试横切链 → S4(TDD 先写失败测试) → S5 → S7 |
| 小功能 | 1-3 文件 | S0 → S4(TDD) → S5 → S6(轻量) → S7 |
| 中型功能 | 多模块、需拆步 | S0 → S1 → S3(`writing-plans`) → S4(`subagent-driven`) → S5-S7 |
| 大型特性/新系统 | 跨层、高风险、需求模糊 | 全流程：S0→S1→S2(speckit)→S3(+多角色会审)→S4→S5→S6(interrogate+production-risk-review)→S7(ship)→S8 |
| 疑难杂症/大迁移 | 跨周、需审计 | `figure-it-out` / `blueprint-driven-development` 剧本模式 |

---

## 五、冗余去重清单（已执行 ✅ 2026-08-22）

| 重复组 | 处置 | 结果与证据 |
|---|---|---|
| TDD ×4 | `coding/test-driven-development` 为 canonical（通用入口）；`coding/tdd-workflow` 收窄为"用户显式要求覆盖率门禁/完整测试金字塔"时才触发；`engineering/tdd` 收窄为"用户显式提 red-green-refactor / 测试质量 / seams / mock"时才触发；`pstack/tdd` 经核实描述本已收窄，免改 | 两个 SKILL.md 的 description 已改，正文未动 |
| Google 风格审查 ×2 | 删除源目录 `coding/google-style-code-review/`；保留 `workflow/google-code-review` | 前次决策（见 implementation-notes.md）已将其加入 sync.sh `DUPLICATE_SKILL_NAMES` 隐藏同步；本次删源目录完成闭环，防护条目保留以防 `--discover` 再导入 |
| 西域 PR 审查 ×2 | 删除旧版 `imported/code-review/`（v1.0.0）；保留 `workflow/xiyu-code-review`（334+ 行，含 ArchUnit 11 条规则） | `engineering/code-review/code-review` 原是指向 imported 的符号链接，悬空后一并删除 |
| continuous-learning ×2 | 删除 `workflow/continuous-learning/` 残留（无 SKILL.md，仅散落脚本）；保留 `misc/continuous-learning(+v2)` | 索引中仅剩 misc 版条目 |
| strategic-compact 残留 | 删除 `architecture/strategic-compact/`（仅 suggest-compact.sh，无 SKILL.md）；保留 `misc/strategic-compact` | 索引中仅剩 misc 版条目 |
| code-review 多份 | **澄清非重复**：`engineering/code-review`（双轴 Standards+Spec 并行审查）与 `workflow/xiyu-code-review`（西域定制版）功能不同，均保留；真正重复的只有 imported 旧副本（上条已删） | 通用双轴审查以 engineering 为 canonical |

**传播与验证**：删除完成后运行 `./sync.sh`，全部目标同步成功——SKILLS-INDEX.md 与 GEMINI.md 自动重建（`google-style-code-review`、旧版 `code-review` 条目消失，canonical 条目齐全），`~/.claude`、`~/.codex`、`~/.trae-cn`、`~/.agents` 四个同步目录经检查无残留链接。

> 原则不变：**去重只动 description 触发词与目录归属，不改写技能正文**——保住跟随上游更新的能力。

---

## 六、六范式贡献对照

| 范式 | 主要贡献给生命周期的段落 |
|---|---|
| superpowers | S0-S3-S7 的骨架链条与"技能互相引用成链"的组织方式 |
| speckit | S2 的严谨规格流（constitution/specify/clarify/analyze） |
| gstack | S3 多角色计划评审、S6 QA、S7 ship/canary 交付链 |
| omc | S4 执行引擎（subagent/ralph/autopilot）、四阶段总纲（standard-workflow 即其简化版） |
| pstack/poteto | 横切原则层、playbook 按场景分发思想、S3 architect/arena |
| matt pocock | S2 to-spec 轻量路线、S4 implement、S6 双轴审查 |

---

## 七、验证计划（怎么证明这张地图是对的）

1. **存在性校验**：表中引用的全部技能路径必须真实存在（已对照 Glob 结果编写，router 化时再机器复核一遍）。
2. **实战校验**：取 3 个真实任务各跑一遍对应路由——① 一个微改动（快速路径）② 一个中型功能（writing-plans → subagent → verification）③ 一个大型特性（speckit 全流程 + 会审）。
3. **对照指标**：返工次数、验证证据完整度、context 消耗，与传统单技能方式对比。
4. **迭代门槛**：只有实战出现失败证据，才允许增加复杂度（新增阶段/新部门禁）；否则冻结当前粒度。

## 八、下一步（2026-08-22 更新）

1. ✅ 薄 router 元技能已创建：`workflow/unified-dev-flow`——39 个被引用技能名全部机器校验存在，quick_validate 结构验证通过，sync.sh 已传播到全部同步目标（SKILLS-INDEX / GEMINI.md 均收录）；
2. ✅ 第五节去重清单已执行完毕（结果见第五节表格）；
3. ⬜ 用第七节实战校验跑 3 个真实任务并记录结果（微改动 / 中型功能 / 大型特性各一）。
