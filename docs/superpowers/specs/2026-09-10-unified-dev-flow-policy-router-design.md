# Unified Dev Flow 第一期：Policy Router 重构设计

**日期：** 2026-09-10
**状态：** 待用户复核
**范围：** 只重构 Router/Policy；不实现 Gate Kernel、统一 Ledger、执行引擎或 Herdr 适配器

## 1. 背景与结论

当前 `unified-dev-flow` 已经覆盖 S0–S8、入口门禁、验证、审查和交付，但路由模型把任务意图、工作规模和风险混在同一张任务类型表里。结果是同一项工作可能同时属于 Bug、Micro、Security Critical 和 Production，却只能命中一条预制路线；规划深度也因此错误地决定了验证与审查深度。

第一期将它重构为 **policy-driven workflow router**：拥有路由决策、门禁语义和证据规则，继续把具体方法委托给现有技能与工作流引擎。它仍是薄路由器，不在 `SKILL.md` 中实现 brainstorm、spec、TDD、review 或多代理调度逻辑。

## 2. 目标与非目标

### 目标

1. 在任何承诺文件范围和验证路径之前完成只读侦察。
2. 用正交维度组合路线，而不是从互斥任务类型中选择一条路线。
3. 让复杂度只决定规划深度，让风险独立决定验证和审查深度。
4. 明确一个时刻只能有一个工作流控制器拥有执行循环。
5. 用适合不同意图的 Proof Mode 取代通用的 failing-test-first。
6. 明确源码变更后的证据失效与 `S6 → S4 → S5 → S6` 返工闭环。
7. 让交付终点由用户授权的 `delivery_target` 决定。
8. 让 Spec Kit、OpenSpec 和本地轻量规格成为互斥的 Spec Adapter。

### 非目标

- 不创建 `.unified-dev-flow/runs/`，不迁移现有 `.omc/` 或 `.superpowers/` 状态。
- 不实现事件日志、状态机、Task Contract 或 Provider 接口。
- 不接入 Herdr；Herdr 保持未来的执行后端。
- 不删除或改写被路由技能的内部方法。
- 不要求本仓库创建 `.codegraph/`。

## 3. 顶层不变量

重构后的技能开头采用以下原则：

1. **Resume before classification.** 先判断是否存在可安全恢复的工作。
2. **Read before committing.** 先做只读侦察，再承诺范围、测试和命令。
3. **Intent selects the base route.** 意图选择基础生命周期。
4. **Complexity determines planning depth.** 复杂度只调整规格和规划深度。
5. **Risk determines assurance depth.** 风险独立调整验证和审查强度。
6. **One controller owns execution at a time.** 同一时刻只有一个主循环控制器。
7. **Source changes invalidate intersecting evidence.** 相关源码变化使旧验证证据失效。
8. **No completion claim without fresh evidence.** 没有最新证据不得声明完成。
9. **Delivery never exceeds authorization.** 不得超过用户授权的交付终点。

## 4. 启动顺序

```text
R0 Read-only Recon
  ↓
Resume Gate
  ├─ MATCH → 恢复既有控制器与阶段
  ├─ COMPATIBLE_DRIFT → 对账后恢复
  ├─ CONFLICTING_DRIFT → 作废冲突状态，重新进入 Entry Gate
  └─ FRESH → Entry Gate
                 ↓
          Policy Resolution
                 ↓
          Selected Controller
                 ↓
             S0–S8 子集
```

### 4.1 R0 Read-only Recon

R0 允许读取，不允许修改。最小检查集合：

- 当前目录、Git 状态、分支、近期提交和 worktree 状态；
- `AGENTS.md`、`RULES.md`、`CLAUDE.md`、`lessons-learned.md` 等约束；
- 未完成 workflow ledger、活跃 spec/change 和已有计划；
- 项目清单与测试入口，如 `package.json`、`pyproject.toml`、构建文件；
- `.specify/`、`openspec/` 及项目声明的 spec backend；
- 与需求直接相关的代码、测试和调用路径。

`.codegraph/` 是**每个目标项目自己的可选索引**：存在时按照项目 `AGENTS.md` 优先使用 CodeGraph 定位符号和调用路径；不存在时正常使用 `rg`、文件读取等工具。Router 不负责初始化它，当前 `universal-skills` 仓库没有该目录不构成缺陷。

R0 禁止 Edit、Write、`apply_patch`、生成 migration 或其他会改变工作区的动作。

### 4.2 Resume Gate

第一期只定义语义，不实现新 ledger。恢复判断至少比较：

- task/goal 指纹；
- branch、worktree；
- 已记录 base/head 与当前 HEAD；
- 与任务相关的 diff；
- 当前控制器及其原生状态。

阶段一兼容读取现有 `.superpowers/sdd/progress.md`、`.specify/`、`openspec/changes/` 和已存在的控制器状态。框架中立的统一 ledger 留到第二期。

### 4.3 Entry Gate

保留现有四节机械契约，避免第一期破坏已经安装的 hook：

1. 理解和假设；
2. 最小方案与文件范围；
3. 范围纪律；
4. 验证计划。

语义调整为：这些内容必须基于 R0 证据。第四节填写 `proof_mode + baseline/reproduction + verification commands`，不再对所有任务强制写“失败测试”。`delivery_target` 记录在第一节或第二节。既有 `.omc/entry-gate-<session>.md` 路径在第一期保持兼容；第二期再决定迁移策略。

## 5. 六维 Policy Resolution

Router 生成的是一份组合决策，而不是单选任务类型：

```yaml
resume: fresh | match | compatible_drift | conflicting_drift
intent: bug | feature | refactor | migration | research | config
complexity: micro | small | medium | large | intractable
risk: [auth, permission, security, money, data_integrity, production, state_machine, concurrency, migration]
domain: [ui, api, database, performance, docs, infrastructure]
delivery_target: patch | working_tree | commit | pr | merge | deploy
spec_backend: unified | speckit | openspec
controller: <exactly one controller or none>
proof_mode: <derived from intent and domain>
assurance_level: deterministic | adversarial | mutation
```

### 5.1 Intent：选择基础路线

| Intent | 基础路线 |
|---|---|
| bug | S0 → debug → S4 → S5 → S6 → S7(target) |
| feature | S0 → S1/S2/S3（按复杂度裁剪）→ S4 → S5 → S6 → S7(target) |
| refactor | S0 → S3 → S4 → S5 → S6 → S7(target) |
| migration | S0 → S2/S3 → S4 → S5 → S6 → S7(target) |
| research | S1 → S3 → S8，停止，不进入交付 |
| config | S0 → S4 → S5 → 按风险决定 S6 → S7(target) |

UI、性能、安全等不再作为互斥 intent；它们作为 domain 或 risk 叠加到基础路线。

### 5.2 Complexity：只决定规划深度

| Complexity | 规划策略 |
|---|---|
| micro | Entry Gate 中的文件清单即压缩计划 |
| small | 简短实现步骤，无独立重型 spec |
| medium | 需要书面 spec/plan/tasks；解析一个 Spec Adapter |
| large | 完整规格、计划会审、任务切片和阶段 checkpoint |
| intractable | playbook、审计轨迹和人工升级点 |

复杂度不得降低由风险要求的验证或审查。

### 5.3 Risk：决定 Assurance 深度

- 无高风险信号：Level 1，确定性验证。
- auth、permission、security、money、data integrity、state machine、关键并发：至少 Level 2，对抗验证。
- 支持 mutation runner 的核心业务逻辑：Level 3，真实 mutation testing。
- CSS、布局、配置、生成代码、migration glue 等不强制伪 mutation；使用其领域对应的确定性或对抗证据。

### 5.4 Domain：加载适配技能

Domain 只增加相关 specialist，不改变 Controller Ownership。例如 UI 加载 `frontend-design`，性能加载 `performance-tuning`，数据访问加载 `access-pattern-driven-data-modeling`。

### 5.5 Delivery Target：限定终点

`delivery_target` 是授权上限：

- `patch`：只返回补丁建议，不写工作区；
- `working_tree`：修改并验证，停在本地工作区；
- `commit`：允许创建本地提交；
- `pr`：允许推送并创建 PR；
- `merge`：允许合并，但不自动部署；
- `deploy`：允许经过生产门禁后部署。

用户只说“修复/实现”时默认 `working_tree`。任何升级都需要用户明确授权；S7 的定义改为 **Fulfill delivery target**。

## 6. Controller Ownership

角色分为：

- **Controller**：拥有主循环、重试、暂停和终止条件；
- **Stage Skill**：完成某个阶段，不拥有全局循环；
- **Worker**：执行被分派任务；
- **Reviewer**：独立判断，不修改被审源码；
- **Principle**：约束所有角色；
- **Domain Specialist**：提供领域方法。

控制器候选包括 `speckit-chain`、OpenSpec change flow、`executing-plans`、`autopilot`、`ralph`、`team` 和 `figure-it-out`。同一时刻最多一个 Controller；它可以调用 Worker、Reviewer 或 Stage Skill，但只有在记录明确的 handoff 后才能把控制权交给另一个 Controller。

OMC 已删除的 `swarm` alias 与本仓库的 pstack `swarm` 技能不是同一对象。第一期不删除本地技能；在文档中使用明确命名和角色分类，避免把 OMC 兼容别名当作本地 fan-out worker 工具。

## 7. Spec Adapter Resolution

Spec backend 必须单选，解析顺序如下：

1. 可安全恢复的活跃 change/spec 保持原 backend；
2. 用户明确指定且目标项目已具备的 backend；
3. 项目配置声明的 backend；
4. 仅检测到一个已初始化 backend 时选它；
5. 同时检测到 `.specify/` 与 `openspec/` 且无明确所有权时，停止并要求选择；
6. 均未初始化时使用 Unified Dev Flow 轻量默认路径。

不得让 Spec Kit 与 OpenSpec 维护同一需求。

Spec Kit adapter 更新为完整的可裁剪阶段集合：`ensure constitution → specify → clarify → plan → checklist → tasks → analyze → implement slices → converge`。Constitution 默认只读；仅在缺失或用户明确改变项目原则时创建/更新。大型工作由同一 Controller 分片执行并设置 checkpoint，不再称为 one-shot。

OpenSpec adapter 根据目标项目已安装 profile 解析 core 或 expanded flow，不在 Router 中写死固定命令数量。

## 8. Proof Before Change

| 场景 | First proof |
|---|---|
| Bug | 失败测试或稳定复现脚本 |
| Feature | 尚未满足的 acceptance test |
| Refactor | 修改前通过的 characterization/regression baseline |
| Migration | dry-run、forward 和 rollback 验证 |
| Performance | 可复现 benchmark baseline |
| Security | exploit/repro 或安全断言 |
| Config | schema、lint 或配置加载验证 |
| UI | visual/E2E acceptance evidence |

TDD 仍是 Bug 和 Feature 的默认实现方法，但不再被错误地套用于所有意图。

## 9. Scope Discipline

每个变更文件必须映射到以下至少一项：

1. requested behavior；
2. root-cause dependency；
3. required test；
4. required migration/build artifact。

其他发现只记录。若修复根因必须扩大范围，先 amend Entry Gate，再修改文件；“直接相关”不再被解释为禁止触及真正的根因依赖。

## 10. 验证证据与 Review 闭环

验证分三级：

1. **Deterministic**：构建、测试、lint、schema、dry-run 等真实命令；
2. **Adversarial**：权限反例、边界条件、跨层一致性、攻击或状态转换反例；
3. **Mutation**：仅在合适且有真实 runner 的核心逻辑上执行。

状态闭环固定为：

```text
S4 Implement/Fix
  ↓
S5 Fresh Verification
  ↓
S6 Independent Review
  ├─ MERGE_READY → S7(target)
  └─ NEEDS_FIXES → S4 → S5 → S6
```

任何源码或测试变化都使依赖范围相交的验证结果和 review verdict 失效。Reviewer 输入以 spec、diff、tests 和 evidence 为主，不默认继承 Implementer 的完整思考过程；Reviewer 只判断，修复仍由 S4 角色完成。最多三轮 NEEDS_FIXES，之后升级人工。

## 11. 第一期开工文件范围

实现阶段预计修改：

- `MOD: categories/workflow/unified-dev-flow/SKILL.md`
- `MOD: categories/workflow/unified-dev-flow/references/enforcement.md`
- `NEW: categories/workflow/unified-dev-flow/references/policy-model.md`
- `NEW: categories/workflow/unified-dev-flow/scripts/test_router_policy.py`
- `MOD: WORKFLOW-MAP.md`
- 自动同步产物与技能元数据仅由 `./sync.sh` 按仓库既有规则生成。

`entry-gate-check.py` 的四标题与文件范围机械检查在第一期保持兼容；只有测试证明现有 checker 无法支持新语义时才扩大到该脚本，并先 amend Entry Gate。

## 12. 验收标准

1. `SKILL.md` 不再出现 “Scale decides depth” 或互斥 Task Type 路由表。
2. R0 明确先于 Resume、Entry 和 Policy Resolution；`.codegraph/` 仅为项目级可选能力。
3. 文档中有且只有一条 Single Controller invariant。
4. Micro + Security + Production 能组合为轻规划、重验证、重审查，并停在用户授权的 delivery target。
5. Bug、Feature、Refactor、Migration、Performance、Config、UI 都有明确 Proof Mode。
6. 所有 NEEDS_FIXES 路径都明确回到 S4 后重新经过 S5。
7. `Large-feature one-shot` 和默认 `Merged, deployed` 被移除。
8. Spec Kit/OpenSpec backend 互斥，双初始化且无归属时 fail closed。
9. OMC legacy swarm 与本地 pstack swarm 被明确区分。
10. Router 保持薄：只引用技能/适配器，不复制它们的内部实现。

## 13. 验证命令

实现完成后至少运行：

```bash
python3 categories/workflow/unified-dev-flow/scripts/test_router_policy.py
python3 categories/workflow/unified-dev-flow/scripts/test_entry_gate_check.py
python3 categories/.system/skill-creator/scripts/quick_validate.py categories/workflow/unified-dev-flow
git diff --check
./sync.sh
```

同步后再次运行静态策略测试，并检查 `SKILLS-INDEX.md`、`GEMINI.md` 与各同步目标没有悬空链接。

## 14. 被拒绝的替代方案

- **只修几处文案矛盾**：改动最小，但继续保留混合分类模型，下一次仍会出现风险与规模耦合。
- **第一期直接实现统一 Runtime/Ledger**：方向正确，但同时改变 Policy、State 和执行适配器，无法隔离验证；推迟到第二期。
- **删除所有 swarm 引用**：会把已经删除的 OMC alias 与仍然存在的本地 pstack fan-out 技能混为一谈。
- **强制所有项目初始化 CodeGraph**：超出 Router 职责，也违背索引由目标项目自行决定的背景约束。

## 15. 第二期接口预留

第一期文档会稳定以下未来字段，但不实现持久化：`work_id`、policy dimensions、controller、current_stage、scope mapping、proof mode、evidence dependencies、review round、waivers 和 next action。第二期再设计 `.unified-dev-flow/runs/`、Gate Kernel、事件日志和 Adapter Contract，并保留对现有框架状态的迁移兼容层。
