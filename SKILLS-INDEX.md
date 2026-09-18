# SKILLS-INDEX

> 技能来源速查表 · 自动生成于 2026-09-18 08:52 · 共 80 个一级技能。
> 按「来源」检索：公开技能包（外部大神编写的成套技能） / 自建・单个技能。
> 技能由 AI 按 description 自动触发，无需记住名字。

按来源检索：
[一、公开技能包](#一公开技能包) · [二、自建・单个技能](#二自建单个技能)

## 一、公开技能包
_外部技术大神编写的成套技能，每个包内部技能有使用逻辑。_

### Spec Kit
_需求→架构规范→任务清单的标准化开发套件_

**spec-kit** _(Spec Kit 需求规范与工单套件)_

| 技能 | 用途 |
| --- | --- |
| `speckit-analyze` | Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation. |
| `speckit-chain` | 一键串行执行 spec-kit 完整开发工作流：constitution → specify → [clarify] → plan → [validate] → tasks → [analyze] → implement。 严格按照官方 spec-kit 方法论串联 5 个核心命令 + 3 个官方推荐的质量门禁。 触发词：全流程开发、全程开发、speckit 全流程、串行执行 speckit、用 spec kit 走完整套流程、帮我实现一个功能并用 speckit。 非单步调试场景——如果用户只想执行其中某一步，应使用对应的独立技能而非本 chain skill。 |
| `speckit-clarify` | Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec. |
| `speckit-constitution` | Create or update the project constitution from interactive or provided principle inputs. |
| `speckit-git-feature` | Create a feature branch with sequential or timestamp numbering |
| `speckit-git-initialize` | Initialize a Git repository with an initial commit |
| `speckit-implement` | Execute the implementation plan by processing and executing all tasks defined in tasks.md |
| `speckit-plan` | Execute the implementation planning workflow using the plan template to generate design artifacts. |
| `speckit-specify` | Create or update the feature specification from a natural language feature description. |
| `speckit-tasks` | Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts. |

### anthropics 官方工具
_安装能力 / 文档 / PDF / 浏览器工具_

**.system** _(元工具（创建 / 安装技能）)_

| 技能 | 用途 |
| --- | --- |
| `skill-creator` | 创建或更新 AI 技能文件夹以扩展工具能力 |

### gstack 发行版
_Everything Claude Code 全家桶定制技能_

**gstack** _(gstack 发行版定制技能)_

| 技能 | 用途 |
| --- | --- |
| `browse` | Fast headless browser for QA testing and site dogfooding. (gstack) |
| `canary` | Post-deploy canary monitoring. (gstack) |
| `context-restore` | Restore working context saved earlier by /context-save. (gstack) |
| `context-save` | Save working context. (gstack) |
| `cso` | Chief Security Officer mode. (gstack) |
| `health` | Code quality dashboard. (gstack) |
| `investigate` | Systematic debugging with root cause investigation. (gstack) |
| `plan-eng-review` | Eng manager-mode plan review. (gstack) |
| `ship` | Ship workflow: detect + merge base branch, run tests, review diff, bump VERSION, update CHANGELOG, commit, push, create PR. (gstack) |
| `spec` | Turn vague intent into a precise, executable spec in five phases. (gstack) |

### mattpocock / skills
_需求→规格→工单→实现→验证的完整工程闭环_

**engineering** _(mattpocock 工程技能)_

| 技能 | 用途 |
| --- | --- |
| `code-review` | 按规范与需求双轴并行审查分支改动并对比报告 |
| `domain-modeling` | 沉淀领域术语并记录架构决策以构建统一语言 |
| `prototype` | 构建一次性原型验证设计方案与逻辑是否合理 |
| `to-spec` | 把当前对话综合成规格并发布到问题跟踪器 |

### poteto 工程方法论
_poteto-mode 工作流 + 21 条工程原则_

**pstack** _(poteto 工程方法论)_

| 技能 | 用途 |
| --- | --- |
| `architect` | 先勾勒类型与模块结构再进入实现 |
| `figure-it-out` | 为大型迁移设计可审计的执行剧本 |
| `interrogate` | 多模型从独立角度挑战代码并寻找盲点 |
| `show-me-your-work` | 用 TSV 日志保留可审阅的决策轨迹 |
| `swarm` | 并行派出多个工作者并汇总为一份报告 |
| `technical-writing` | 符合作者文档风格的分层技术写作标准 |

### 前端设计
_前端界面设计技能_

**ui-ux** _(前端设计)_

| 技能 | 用途 |
| --- | --- |
| `frontend-design` | 打造高质量且有辨识度的前端界面 |
| `motion-design` | Applies motion design principles to create emotionally-driven, technically sound animations and transitions. Provides timing, easing, choreography, and Disney animation principles adapted for UI. Use when creating animations, transitions, micro-interactions, loading states, page transitions, scroll-triggered effects, or any motion work. Works with CSS, Framer Motion, GSAP, Lottie, Spring, or any animation system. |
| `ui-ux-pro-max` | 覆盖多风格多栈的 UI/UX 设计智能库 |

---

## 二、自建・单个技能
_自己创建或单独引入的技能，按原分类组织。_

### architecture
_架构模式_

| 技能 | 用途 |
| --- | --- |
| `access-pattern-driven-data-modeling` | 依据访问模式设计数据库表、索引与查询路径 |
| `cog-4d-audit` | 对已通过 CI 的代码做四维深度审查揪出隐藏缺陷 |

### coding
_编码规范与模式_

| 技能 | 用途 |
| --- | --- |
| `ai-release-engineer` | Use when AI-generated code is ready for validation, merge, release, or production deployment; before PR merge verification, test/UAT/production promotion, canary or full rollout, or post-release rollback decisions. |
| `api-design` | 设计生产级 REST API 并规范命名、状态码与分页 |
| `clean-code-behavior-preserving-refactoring` | 行为保持重构：删减优先、合并重复并证明行为未变（含原极简重构策略） |
| `performance-tuning` | 针对高 CPU、内存与锁竞争场景做性能优化 |
| `self-verifying-tests` | 编写跨层自验证测试核对 UI、数据库与代码一致性 |
| `test-driven-development` | 实现功能前先写失败测试并遵循 TDD 方法论 |
| `typesafe-ai` | 基于 TypeSafe System One 模型（Jev）将自然语言与应用状态转换为类型化判断与概率决策原语 |

### debugging
_调试方法论_

| 技能 | 用途 |
| --- | --- |
| `paranoid-debugging` | 对生产关键代码做证据驱动的高强度再验证 |
| `root-cause-hunter` | 逆向追踪调用链定位问题源头并证明 bug 必然发生 |
| `systematic-debugging` | 遇到 bug 或异常时先系统诊断再提出修复方案 |

### deployment
_部署模式_

| 技能 | 用途 |
| --- | --- |
| `database-migrations` | 跨数据库的迁移、回滚与零停机部署最佳实践 |
| `deployment-patterns` | CI/CD、Docker 容器化与生产就绪检查的部署流程 |
| `xiyu-server-deploy` | 西域投标平台服务器部署、健康检查与回滚预案 |

### misc
_其他_

| 技能 | 用途 |
| --- | --- |
| `strategic-compact` | 在合理节点手动压缩上下文以保留信息 |

### refactoring
_重构实践_

| 技能 | 用途 |
| --- | --- |
| `ai-slop-cleaner` | Clean AI-generated code slop with a regression-safe, deletion-first workflow and optional reviewer-only mode |
| `entropy-reduction` | 设计边界清晰且低复杂度的模块化代码 |

### security

| 技能 | 用途 |
| --- | --- |
| `security-review` | Use this skill when adding authentication, handling user input, working with secrets, creating API endpoints, or implementing payment/sensitive features. Provides comprehensive security checklist and patterns. |

### testing
_测试_

| 技能 | 用途 |
| --- | --- |
| `e2e-testing` | Playwright 端到端测试与页面对象模型实践 |

### workflow
_开发流程_

| 技能 | 用途 |
| --- | --- |
| `blueprint-driven-development` | 按飞书产品蓝图逐小节实现标讯功能 |
| `blueprint-e2e` | 针对飞书产品蓝图的每一个小节（小节粒度，如 4.2.1、4.3.2），独立编写和执行 Playwright E2E 测试， 验证功能实现是否符合蓝图需求。测试即文档——E2E 测试是对蓝图需求的机器可执行描述。 触发场景：用户提到"E2E 测试蓝图书"、"做蓝图的 E2E"、"测试某小节"、"e2e 覆盖"、"推进 E2E"、 "验证蓝图测试覆盖"、"blueprint E2E"、"蓝图书 e2e"、"补充测试覆盖"、"测试即文档"。 与 blueprint-driven-development 的区别：后者负责"实现"功能，本技能负责"验证"实现是否符合蓝图。 核心原则：每个蓝图小节必须有对应 E2E spec，不存在 = 未完成。 含测试覆盖缺口检测、Playwright 脚本自动生成辅助、CI 门禁绑定。 |
| `brainstorming` | 创造性工作前探索用户意图、需求与设计 |
| `cow-sandbox` | Use when starting non-trivial coding tasks that require workspace isolation without the overhead, branch locks, or residue of git worktrees. Uses macOS APFS (cp -cR) / Linux reflink copy-on-write snapshots for instant, zero-cost sandbox isolation. |
| `create-migration` | 创建 Flyway 数据库迁移脚本（MySQL 8.0），自动检测下一版本号、生成迁移 SQL 和回滚脚本、执行格式校验。当检测到新增或修改数据库表结构需求时自动触发。 |
| `dispatching-parallel-agents` | 并行派发相互独立的任务给多个代理 |
| `executing-plans` | 在独立会话按检查点执行书面实现计划 |
| `github-sync` | GitHub 与 Gitee 双向代码同步技能（西域数智化投标管理平台）。用于 AI Coding 工具（Cursor/Codex/Claude 等）在 GitHub 远端改代码后同步回本地 Gitee 主仓库，或反向推送本地代码到 GitHub 供 AI 工具使用。触发场景：用户提到"同步 GitHub"、"拉取 AI 改动"、"GitHub 代码合回 Gitee"、"推 GitHub 镜像"、"AI Cursor 改的代码怎么拉回来"、"github-sync"、"同步远端 AI 改动"。 |
| `google-code-review` | 执行 Google 风格的代码审查流程 |
| `html-first-workflow` | 以 HTML 优先的工作流开发前端 |
| `knowledge-capture` | 将 session 中的开发/改 bug/架构/需求确认结果按类型沉淀到 docs/。 写 docs/ 不写 .wiki/，严格遵循现有格式，每条知识有明确归属。 |
| `linear-task-creator` | 创建或更新 Linear 任务并套用项目模板 |
| `parse-prd` | 解析飞书 PRD 文档：提取正文、画板、截图、HTML 片段和注释，合并为结构化需求简报。当用户提供飞书 PRD 链接时自动触发。 |
| `production-risk-review` | 对上线系统 PR 做生产风险审计 |
| `pseo` | 执行产品搜索优化相关的流程 |
| `receiving-code-review` | 收到审查反馈时严谨验证而非盲从 |
| `six-step-finish` | 通用六步任务收尾：知识沉淀、Wiki 检查、合并确认（可选 forge）、锚点同步、分支核对与卫生清理 |
| `subagent-driven-development` | 用子代理执行相互独立的实现计划 |
| `ultrawork` | Parallel execution engine for high-throughput task completion |
| `unified-dev-flow` | 当开始非简单的功能开发、修 bug、重构或迁移，需要决定走哪些阶段、调用哪些技能、走多深时使用。当用户问该用什么流程或技能时使用。触发词：统一流程 / 标准流程 / 开发流程 / 完整流程 / 走流程 / 端到端开发 / 该用什么技能 / 帮我选流程 / 怎么推进这个需求 / 规范流程。Use when deciding which dev workflow/skills to use for a non-trivial coding task. |
| `using-git-worktrees` | 用 git worktree 创建隔离的开发工作区 |
| `verification-before-completion` | 声明完成前先运行验证命令并确认结果 |
| `wiki` | LLM Wiki — persistent markdown knowledge base that compounds across sessions (Karpathy model) |
| `writing-plans` | 动代码前为多步任务编写实现计划 |
| `xiyu-code-review` | 按西域投标平台规范审查 PR 的架构与安全 |
| `xiyu-mode` | 西域投标管理平台专属模式（质疑复用优先+SpecKit流程+FP-Java+多Agent收尾） |
