# WORKFLOW-MAP · 统一开发生命周期映射

> 目标：把 speckit / gstack / ohmyclaude(omc) / pstack(poteto) / superpowers / matt pocock 六套范式的精华，
> 编排到**一条统一生命周期**上。统一的是骨架（阶段 + 门禁），不统一的是肌肉（各技能实现）。
>
> 本文档是 `unified-dev-flow` 的仓库映射，2026-09-10 对齐 policy router。
> 详细路由策略以该技能的 `references/policy-model.md` 为唯一权威；`SKILL.md` 是执行入口。本表保留各阶段的技能映射与中文速查，不复制执行器内部流程。
>
> **Canonical（首选）选取标准**：平台中立、描述与参考文档最完整、能与相邻阶段技能自然衔接。
> 备选保留不删除，仅在特定条件下替换首选。

---

## 一、生命周期总览

```
R0 → Resume Gate → Entry Gate → Policy Resolution → Controller → selected S0–S8 stages
Policy Resolution = Resume + Intent + Complexity + Risk + Domain + Delivery

可选阶段：S0 准备 / S1 意图 / S2 规格 / S3 规划 / S4 实现 / S5 验证 / S6 审查 / S7 交付 / S8 沉淀

横切关注点（任何阶段可介入）：
  🎯 领域专项   🔍 调试诊断   🧠 上下文管理   📐 工程原则约束（pstack principle-*）
```

**门禁规则**（借鉴各范式之长）：

- R0 Read-only Recon：先读项目约束、代码、工作区、验证入口和已有状态；shell/read 工具可用，侦察阶段不写文件。已有 `.codegraph/` 时按项目规则使用，不创建索引。
- Resume Gate：分类前比较目标、branch/worktree、记录的 base/head、当前 HEAD、相关 diff 与 controller 状态；FRESH 进 Entry，MATCH 原位续接，COMPATIBLE_DRIFT 先协调证据再续接，CONFLICTING_DRIFT 使冲突状态失效并回 Entry。沿用原生记录，不引入新 runtime/ledger。
- Entry Gate：R0 后提交 4 项入口声明，记录理解、最小文件范围、范围纪律、`proof_mode` 与基线/复现/未满足验收及精确验证命令；首次 Edit/Write 由 hook 机械拦截（契约见 unified-dev-flow `references/enforcement.md`）。续接工作先协调已有 gate；patch 目标仅在回复中提供声明与补丁。
- S1→S2：意图不清不得写规格（speckit clarify 精神）
- S3→S4：先达到 Complexity 要求的规划深度并取得 Proof Before Change；micro 以 Entry 文件清单作压缩计划，small 用简短步骤，large 先通过计划评审。压缩规划不豁免验证。
- S4→S5：声明完成前必须跑真实验证并出示证据（verification-before-completion / prove-it-works 精神）
- S5 assurance：按风险选择 deterministic / adversarial / mutation。auth、permission、security、money、data_integrity、state_machine（关键状态机）和 concurrency 至少 adversarial；mutation 仅用于有真实 runner 的合适核心逻辑。
- S5→S6→S7：live/production 变更在 S7 前过 `production-risk-review`；无人值守交付另需 `ai-release-engineer`。S7 仅履行已授权目标。
- S6 fix-loop：reviewer 只判不改，NEEDS_FIXES 必走 **S6 → S4 → S5 → S6**；三轮 NEEDS_FIXES 后升级给人，不换代理重置计数。源码或测试变更使相交的验证证据和审查结论失效，修复后重新验证、审查。

Controller Ownership Invariant：同一时刻至多一个 Controller 持有执行循环、重试、暂停和终止权，也可不选 Controller。`speckit-chain`、OpenSpec change flow、`executing-plans`、完整 `subagent-driven-development`、`autopilot`、`ralph`、`team`、`figure-it-out` 是候选 owner，主循环不得嵌套；切换前在已有原生记录中明确交接。Stage Skill 执行阶段，Worker 执行委派单元，Reviewer 独立判定，Principle 约束所有角色，Domain Specialist 提供领域方法与证据。

选择或恢复前按 policy-model 的 Controller Eligibility 检查 delivery_target、三轮升级、证据失效和选定 adapter。完整 SDD 在 commit 以下不具资格，除非用户明确选择它并授权所需本地提交；此例外不授权 push/merge/deploy。未适配的 `speckit-chain` 不具资格；不得假定一句覆盖指令能停用其原生章程改写或一次执行全部任务的行为。能力不明时使用其他合格 owner、无 Controller 路线或明确记录交接。

---

## 二、分阶段映射表

### S0 会话准备与环境隔离

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `using-git-worktrees` | 按需创建或使用隔离 worktree；已有合适隔离工作区或纯只读路线不必新建 |
| 备选 | `project-session-manager` | 多工单/多 worktree 并行场景升级替代 |
| 备选 | `recall` | 接续之前的工作时先重建上下文 |
| 辅助 | `deepinit` | 新代码库首次进入时生成分层 AGENTS.md |
| 验证基线 | `health` | S4 前取得适用基线，供 S6 比较 |

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
| **canonical** | 选定的 Spec Adapter（`unified` / `speckit` / `openspec`） | 一个需求只由一个 backend 持有；解析顺序见下文 |
| Spec Kit 适配 | `speckit-specify` + `speckit-clarify` | 仅在选定 Spec Kit 且项目已初始化 `.specify/` 时使用 |
| 轻量适配 | Unified 本地 artifact；有条件使用 `to-spec` | 默认命名本地规格路径（沿用项目惯例或 `docs/specs/<task>.md`），兼容 working_tree；to-spec 仅在明确授权 issue 发布且 tracker/triage labels 已配置时具资格 |
| 备选 | `spec` | 产出物直接是 issue/ticket、要与 GitHub 流衔接时 |
| 配套 | constitution ensure/read-only | 确认并只读现有章程/项目原则；记录所依据文档，缺失时在选定 adapter 下补足必要约束，不因每次任务重复改写章程 |
| 配套 | `domain-modeling` | 有领域建模诉求时沉淀统一语言 |

#### Spec Adapter Resolution

按顺序选择一个 backend：安全可续接的 active backend → 当前环境可用的用户明确选择 → 项目配置 → 唯一已初始化 backend → `unified` light path。如果 `openspec/` 与 `.specify/` 共存且仍无明确归属，停止并请求确认 ownership；二者不得同时维护同一需求。只调用目标环境中可用的 adapter/controller；外部 `speckit-*` 命令要求项目已初始化 Spec Kit，选择 adapter 不授权嵌套执行循环。

constitution 的 `ensure/read-only` 表示先确认治理依据存在并读取；已有且适用的章程直接复用。未使用 Spec Kit 时，Entry Gate §1 实际读过的 AGENTS.md、架构约束等项目文档可作为 governing principles。缺失约束或真实冲突应明确记录并在授权范围内解决，不能将 ensure 解释为每个中型任务都运行 `speckit-constitution` 或重写项目治理。Medium 要求 spec/plan/tasks，通过选定 adapter 满足即可，不规定固定的 Spec Kit 命令链。

Spec Kit 的可裁剪序列由 policy-model 定义：ensure/read-only constitution → specify → clarify → plan → checklist → tasks → analyze → implement slices → converge。章程只在缺失或用户明确改变项目原则时创建/更新；适用的 proof/review/planning 门禁不可裁掉。OpenSpec 解析目标项目已安装的 `core` 或 `expanded` profile，不写死命令数量；未知或不可用的必需能力应停止并报告。已选 backend 不可用时不静默替换，不隐式初始化或升级工具。

### S3 方案规划（怎么做）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `writing-plans` | 动代码前写实现计划，bite-sized 步骤 + 预埋验证点 |
| 架构先行 | `architect`（pstack） | 先勾勒类型签名与模块结构再填实现 |
| 规格计划 | 选定 Spec Adapter；Spec Kit 下为 `speckit-plan` + `speckit-tasks` | medium+ 要求 spec/plan/tasks，large 增加评审和检查点 |
| 计划评审 | `plan-eng-review` / `plan-ceo-review` / `plan-design-review` | 大型特性必过（门禁），其余可选 |
| 一致性检查 | 选定 adapter 的检查；Spec Kit 下为 `speckit-analyze` / `speckit-checklist` | 规格-计划-任务交叉校验 |
| 章程违规检查 | （内置） | 中型以上：plan 无 constitution 违规，或豁免列表已列出（S3 exit 门禁） |
| 原型探路 | `prototype` / `arena` / `principle-exhaust-the-design-space` | 无先例的交互或设计决策，先对比再定案 |
| 数据建模 | `access-pattern-driven-data-modeling` | 涉及建表/改表、加索引、列表/搜索/报表查询路径、反规范化或读模型设计时；从访问模式倒推 schema，每个索引对应具体查询 |

### S4 实现执行（动手做）

**Proof Before Change**：bug 先有失败测试或稳定复现，feature 先有未满足的验收测试，二者默认 TDD；refactor 先取得 characterization/regression 基线，migration 先准备 dry-run 与正向/回滚验证，performance 先有 benchmark，security 先有复现或安全断言，config 使用 schema/lint/load 验证，UI 使用 visual/E2E 验收证据。

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical（bug/feature 方法论）** | `coding/test-driven-development` | RED→GREEN→REFACTOR；其他 intent 使用选定 proof_mode |
| Controller 候选 | `subagent-driven-development` / `executing-plans` | 完整 SDD 或顺序执行必须被选为唯一 owner，或先接受明确交接 |
| Worker 分派 | `dispatching-parallel-agents` / 本地 pstack `swarm` | 独立任务才可并行，由已选 Controller 管理；本地 swarm 与 OMC 已退役别名不同 |
| Controller 候选 | `team` | 选为唯一 owner 后管理多 worker；不能嵌入另一 Controller 的主循环 |
| 直改路线 | `implement`（matt pocock） | 已有规格/ticket 的中小型实现 |
| 无人值守 Controller 候选 | `autopilot` / `ralph` / `figure-it-out` | 唯一 owner；按复杂度记录决策轨迹，交付受 delivery_target 与发布门禁约束 |
| TDD 去重 | ~~`tdd-workflow`~~ `engineering/tdd` `pstack/tdd` | 见「五、冗余去重清单」 |

### S5 验证测试（证明对）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `verification-before-completion` | 完成声明前必须跑命令、看输出、留证据 |
| 原则兜底 | `principle-prove-it-works` | 对真实产物验证，拒绝"编译通过就算完" |
| deterministic | 相关 test/build/lint/schema/dry-run | 运行真实检查，证据必须对应当前变更 |
| adversarial | `self-verifying-tests` 与领域反例 | 授权违规、边界、跨层一致性、攻击复现和状态转换；高风险至少达到此级别 |
| mutation | 合适核心逻辑的真实 mutation runner | 按选定 assurance 判定；reviewer 反例不是 mutation，不强加于 CSS/layout、生成代码、配置或迁移胶水 |
| 测试专项 | `e2e-testing` / `cpp-testing` / `eval-harness` | 按层按语言选用 |
| 验证与修复 | 已选 Controller 管理 | 验证发现问题回 S4 修改，再取得新证据；不另启嵌套主循环 |
| 项目级 | `create-verification-skill` + `maintain-verification-skill` | 把"这个项目怎么验"固化成技能 |

### S6 审查质检（挑毛病）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical（门禁）** | `health` + `google-code-review` | 所有到达 S6 的路线必须执行；health 相对 S4 前基线回退即拦，不可用则用 `codehealth-mcp` 或明确豁免；清理引发变更后重新验证并审查 |
| cross-model | `interrogate`（异 lab） | reviewer 与 implementer 异 lab（环境变量 `PSTACK_REVIEW_MODELS` / `pstack-models.mdc` 指定）；未配置退化同模型强制 `interrogate` |
| fix-loop | NEEDS_FIXES / MERGE_READY / ESCALATE | reviewer 收到 spec/验收标准、当前 diff、tests 和新鲜证据，只判不改；NEEDS_FIXES 走 S6 → S4 → S5 → S6，三轮后 ESCALATE |
| spec 一致性 | `code-review`（engineering） | 有 spec 的路线追加：规范轴 + spec 轴双线并行审查 |
| 对抗审查 | `interrogate` / `cog-4d-audit` | 按 adversarial assurance/risk 或独立 reviewer 不可用时的 fallback 选择 interrogate；复杂度本身不触发 |
| 生产风险 | `production-risk-review` | live/production 变更在 S7 前追加，不替代普通 review |
| 安全 | `security-review` / `gstack-cso` | 清单式安全审查 / OWASP+威胁建模 |
| 影响面 | `blast-radius` | 改动前评估可能破坏什么 |
| QA | `qa-only`（只报不改） | 真机浏览器 QA；修复回 S4 |
| AI 痕迹清理 | `ai-slop-cleaner --review` / `receiving-code-review` | 仅有实际 cleanup/slop/refactor 证据时选择 cleaner；审查保持 reviewer-only，只报不改，修复回 S4 |

### S7 交付集成（Fulfill delivery target）

只完成授权的 `delivery_target`；默认实现请求停在 `working_tree`，更高目标需用户明确授权。调用的交付技能即使支持后续步骤，也必须在目标处停止。

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `finishing-a-development-branch` / `ship` | 按目标选择所需交付步骤：patch / working_tree / commit / pr / merge / deploy |
| 发布工程 | `ai-release-engineer` / `release` | AI 代码合并前的验证门禁 / 仓库规则驱动发布 |
| 部署专项 | `deployment/*`（docker/migrations/deployment-patterns）、项目专属如 `xiyu-server-deploy` | 按项目选用 |
| 上线后 | `canary` | 金丝雀监控与回滚决策 |

### S8 沉淀学习（变聪明）

| 角色 | 技能 | 说明 |
|---|---|---|
| **canonical** | `knowledge-capture` | 按 docs/ 现有格式沉淀开发知识，归属明确 |
| 决策轨迹 | `show-me-your-work` | intractable 必须审计轨迹与 capture；无人值守 Controller 在适用时可选此技能 |
| 自动提炼 | `continuous-learning-v2` | 会话观察 → 本能 → 技能演化（v2 优先于 v1） |
| 回顾复盘 | `gstack-retro` | 周期性工程回顾 |
| 元技能 | `learner` / `reflect` / `automate-me` | 把成功流程固化为新技能 |

research 路线使用 S8；intractable 要求审计轨迹与 S8 capture。large 要求完整规格、评审、切片和 checkpoint，不自动追加 S8。patch 的 capture 保留在回复中，其余目标仅写授权的本地产物。

---

## 三、横切关注点

### 🎯 领域专项（Domain Specialists）

任务命中领域信号时按需加载 Domain Specialists，不改变 Controller ownership；纯非代码领域操作可直接调用专项技能。
SKILL.md 保留压缩版，本表补充阶段候选。完整路由由 Resume、Intent、Complexity、Risk、Domain、Delivery 六个独立维度组合。

| 领域信号 | 首选 | 备选/说明 |
|---|---|---|
| UI 构建/打磨、看板/落地页 | `frontend-design` | `ui-ux-pro-max`（BM25 检索引擎：50+ 风格 / 97 色板 / 57 字体 / 99 UX 准则 / 25 图表） |
| CPU/内存/GC/锁竞争、慢接口 | `performance-tuning` | 内置 profiling 工作流；数据访问慢查询另走 `access-pattern-driven-data-modeling` |
| 行为保持重构（清理/精简/拆分/降嵌套） | `clean-code-behavior-preserving-refactoring` | `entropy-reduction`（模块化熵减：循环依赖、边界重划） |
| 调研/选型，先不写代码 | `research`（一手资料 → Markdown 备忘） | `search-first`（写码前先找现成轮子） |
| 客户交付/正式文档 | `html-first-workflow` | `technical-writing`（Diátaxis 分层规范）/ `gstack-make-pdf` |
| API 设计/改造 | `api-design` | router Cross-cutting 已收录 |
| 数据库方言专项 | `postgres-patterns` / `clickhouse-io` | 同上；漏派证据出现再升级 |

### 🔍 调试诊断（升级路径）

```
systematic-debugging（canonical 入口）
  └─ 升级 root-cause-hunter（逆向追踪证明根因）
       └─ 升级 paranoid-debugging（生产关键代码的证据级再验证）
其他工具：diagnosing-bugs（HITL 循环）/ trace（竞争假设）/ deep-dive / gstack-investigate；
数据访问性能排查（慢查询、索引未命中）走 `access-pattern-driven-data-modeling` 的验证环节（EXPLAIN + 访问模式对照）
```

### 🧠 上下文管理

`principle-guard-the-context-window`（批量路由给子代理）+ `strategic-compact`（节点压缩）+
`context-save/context-restore`（跨会话续接）。

### 📐 原则约束层

pstack 的 21 条 `principle-*` 不属于任何阶段，是**所有阶段共享的约束**（如 subtract-before-you-add、fix-root-causes、sequence-verifiable-units）。Router 引导时作为全局 system prompt 级提示注入。

---

## 四、独立策略维度

### Intent Base Route

| Intent | 基础路径 |
|---|---|
| bug | S0 → debug → S4 → S5 → S6 → S7(target) |
| feature | S0 → S1/S2/S3（按 Complexity 裁剪）→ S4 → S5 → S6 → S7(target) |
| refactor | S0 → S3 → S4 → S5 → S6 → S7(target) |
| migration | S0 → S2/S3 → S4 → S5 → S6 → S7(target) |
| research | S1 → S3 → S8；不交付，止 |
| config | S0 → S4 → S5 → 按 Risk 要求 S6 → S7(target) |

### Complexity / Planning

| Complexity | 规划深度 |
|---|---|
| micro | Entry Gate 的文件清单即压缩计划 |
| small | 简短实现步骤 |
| medium | 经一个 Spec Adapter 形成书面 spec、plan、tasks |
| large | 完整规格、计划评审、任务切片与检查点 |
| intractable | playbook、审计轨迹与人工升级点 |

Complexity 只决定规划深度，不能降低 Risk 要求的 assurance。组合路由时保留对应规划要求；不把 micro 解释为门禁豁免。

### Risk / Assurance

| 风险信号 | Assurance / 门禁 |
|---|---|
| 一般变更 | deterministic：相关真实验证命令 |
| auth / permission / security / money / data_integrity / state_machine / concurrency | 至少 adversarial：反例、边界、违规与关键状态机转换证据 |
| 适合 mutation 的核心逻辑且有真实 runner | 可选 mutation；运行真实测试，不以 reviewer 反例冒充 |
| migration | dry-run、正向与回滚验证；涉及数据完整性时至少 adversarial |
| production | S7 前追加 production-risk-review；其他风险所需 assurance 仍保留 |

### Domain Adapter

| Domain | 专项方法与证据 |
|---|---|
| ui | `frontend-design` / `ui-ux-pro-max`；visual/E2E 验收 |
| api | `api-design` |
| database | `access-pattern-driven-data-modeling`；需要时 `create-migration` / `database-migrations` |
| performance | `performance-tuning`；可复现 benchmark 基线 |
| docs | `technical-writing` / `html-first-workflow` |
| infrastructure | `deployment-patterns`；迁移时追加 `database-migrations` |

### Delivery Target

| delivery_target | 授权终点 |
|---|---|
| patch | 仅返回建议补丁，整个流程不写 worktree 或 gate artifact |
| working_tree | 本地修改、验证并停在工作区（默认实现目标） |
| commit | 创建本地提交 |
| pr | 允许 push 并创建 PR |
| merge | 允许合并 |
| deploy | 通过适用生产门禁后允许部署 |

路由决定同时写明 stage subset、spec_backend、Controller（一个或无）、proof_mode、assurance_level、delivery_target。示例：Bug + Micro + Security + Production = 轻规划 + adversarial 验证 + 生产风险审查，最终停在用户授权的交付目标。

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

1. **存在性校验**：本仓库内的技能引用必须真实存在；`speckit-*` 是外部 spec-kit 命令，不计入本仓库技能清单，使用前必须确认项目已初始化 `.specify/`。
2. **实战校验**：取 3 个真实任务各跑一遍组合路由——① micro 安全 bug（轻规划 + 对抗证据）② medium 功能（一个 spec adapter + spec/plan/tasks）③ large 特性（完整规划 + 会审 + 检查点）；均验证 delivery_target 与 controller ownership。
3. **对照指标**：返工次数、验证证据完整度、context 消耗，与传统单技能方式对比。
4. **迭代门槛**：只有实战出现失败证据，才允许增加复杂度（新增阶段/新部门禁）；否则冻结当前粒度。

## 八、历史进展（2026-08-23 记录，路由语义以当前策略为准）

1. ✅ 薄 router 元技能已创建：`workflow/unified-dev-flow`——本地技能引用已机器校验，外部 `speckit-*` 命令已明确标注依赖 `.specify/`；quick_validate 结构验证通过，sync.sh 已传播到全部同步目标（SKILLS-INDEX / GEMINI.md 均收录）；
2. ✅ 第五节去重清单已执行完毕（结果见第五节表格）；
3. ✅ 领域分派轴上线（2026-08-23）：SKILL.md Cross-cutting 新增 Domain specialists（UI / 性能 / 重构 / 调研 / 文档），Step 2 指令改为"阶段技能 + 领域专项"并行加载，"Load only" 眼罩指令移除；路由测试 7 场景全 PASS——规模轴 3（建表中型功能、AI 发布双门禁、错别字豁免）+ 领域轴 4（重构 / UI 看板 / CPU 内存性能 / 纯调研，修复前全 GAP、修复后全 PASS）；
4. ⬜ 用第七节实战校验跑 3 个真实任务并记录结果（微改动 / 中型功能 / 大型特性各一）；
5. ⬜ map 领域表中 DB 方言行（`postgres-patterns` / `clickhouse-io`）仅在实战出现漏派证据时升级进 SKILL.md。
