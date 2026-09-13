# Universal Skills

You have access to a curated set of Universal Skills stored in `~/universal-skills/categories/`.
When the user invokes a skill by name (e.g. "use tdd-workflow", "用 security-review"), read the full `SKILL.md` from the path below and follow its instructions precisely.

**Skills root:** `~/universal-skills/categories/`
**File to read per skill:** `<root>/<category>/<skill-name>/SKILL.md`

---

## Available Skills
### 🛠️ .system
_元工具（创建 / 安装技能）_

| 技能 | 用途 |
| --- | --- |
| `skill-creator` | 创建或更新 AI 技能文件夹以扩展工具能力 |
| `skill-installer` | 从列表或 GitHub 仓库安装技能到本地工具目录 |

### 🏗️ architecture
_架构模式_

| 技能 | 用途 |
| --- | --- |
| `access-pattern-driven-data-modeling` | 依据访问模式设计数据库表、索引与查询路径 |
| `architecture-defense` | 自动拦截错误依赖与分层违规以守护架构边界 |
| `cog-4d-audit` | 对已通过 CI 的代码做四维深度审查揪出隐藏缺陷 |

### 💻 coding
_编码规范与模式_

| 技能 | 用途 |
| --- | --- |
| `ai-release-engineer` | Use when AI-generated code is ready for validation, merge, release, or production deployment; before PR merge verification, test/UAT/production promotion, canary or full rollout, or post-release rollback decisions. |
| `api-design` | 设计生产级 REST API 并规范命名、状态码与分页 |
| `backend-patterns` | Node.js、Express、Next.js 后端架构与 API 最佳实践 |
| `clean-code-behavior-preserving-refactoring` | 行为保持重构：删减优先、合并重复并证明行为未变（含原极简重构策略） |
| `coding-standards` | TS、JS、React、Node 通用编码规范与最佳实践 |
| `content-hash-cache-pattern` | 用 SHA-256 内容哈希缓存昂贵的文件处理结果 |
| `frontend-patterns` | React 与 Next.js 前端开发、状态管理与性能优化 |
| `performance-tuning` | 针对高 CPU、内存与锁竞争场景做性能优化 |
| `regex-vs-llm-structured-text` | 在正则与 LLM 之间选择结构化文本解析方案 |
| `self-verifying-tests` | 编写跨层自验证测试核对 UI、数据库与代码一致性 |
| `tdd-workflow` | 强制 TDD 开发并覆盖单元、集成与端到端测试 |
| `test-driven-development` | 实现功能前先写失败测试并遵循 TDD 方法论 |

### 🗄️ data
_数据 / 数据库模式_

| 技能 | 用途 |
| --- | --- |
| `clickhouse-io` | ClickHouse 查询优化与高性能分析数据工程实践 |
| `postgres-patterns` | PostgreSQL 查询优化、表设计、索引与安全实践 |

### 🐛 debugging
_调试方法论_

| 技能 | 用途 |
| --- | --- |
| `paranoid-debugging` | 对生产关键代码做证据驱动的高强度再验证 |
| `root-cause-hunter` | 逆向追踪调用链定位问题源头并证明 bug 必然发生 |
| `systematic-debugging` | 遇到 bug 或异常时先系统诊断再提出修复方案 |

### 🚀 deployment
_部署模式_

| 技能 | 用途 |
| --- | --- |
| `database-migrations` | 跨数据库的迁移、回滚与零停机部署最佳实践 |
| `deployment-patterns` | CI/CD、Docker 容器化与生产就绪检查的部署流程 |
| `docker-patterns` | Docker 与 Compose 的开发、安全与多服务编排模式 |
| `xiyu-server-deploy` | 西域投标平台服务器部署、健康检查与回滚预案 |

### 🧩 engineering
_mattpocock 工程技能_

| 技能 | 用途 |
| --- | --- |
| `code-review` | 按规范与需求双轴并行审查分支改动并对比报告 |
| `codebase-design` | 共享深层模块设计词汇以改进接口与可测试性 |
| `diagnosing-bugs` | 针对疑难 bug 与性能回归的循环诊断流程 |
| `domain-modeling` | 沉淀领域术语并记录架构决策以构建统一语言 |
| `grill-with-docs` | 通过追问访谈打磨方案并同步产出 ADR 与词汇表 |
| `implement` | 根据规格说明或工单实现具体工作项 |
| `prototype` | 构建一次性原型验证设计方案与逻辑是否合理 |
| `research` | 检索权威一手资料并将调研结论写成 Markdown 备忘 |
| `resolving-merge-conflicts` | 解决进行中的 git 合并或变基冲突 |
| `setup-matt-pocock-skills` | 工程技能首次使用前配置问题跟踪器与领域文档 |
| `tdd` | 先写测试再实现功能并遵循红绿重构循环 |
| `to-spec` | 把当前对话综合成规格并发布到问题跟踪器 |
| `to-tickets` | 把计划或规格拆解成带阻塞关系的工单 |
| `triage` | 对工单与外部 PR 进行分类校验并生成代理简报 |

### 🧙 gstack
_gstack 发行版定制技能_

| 技能 | 用途 |
| --- | --- |
| `_gstack-command` | Router for the gstack skill suite. (gstack) |
| `autoplan` | Auto-review pipeline — reads the full CEO, design, eng, and DX review skills from disk and runs them sequentially with auto-decisions using 6 decision principles. (gstack) |
| `benchmark` | Performance regression detection using the browse daemon. (gstack) |
| `benchmark-models` | Cross-model benchmark for gstack skills. (gstack) |
| `browse` | Fast headless browser for QA testing and site dogfooding. (gstack) |
| `canary` | Post-deploy canary monitoring. (gstack) |
| `careful` | Safety guardrails for destructive commands. (gstack) |
| `codex` | OpenAI Codex CLI wrapper — three modes. (gstack) |
| `context-restore` | Restore working context saved earlier by /context-save. (gstack) |
| `context-save` | Save working context. (gstack) |
| `cso` | Chief Security Officer mode. (gstack) |
| `design-consultation` | Design consultation: understands your product, researches the landscape, proposes a complete design system (aesthetic, typography, color, layout, spacing, motion), and generates font+color preview... (gstack) |
| `design-html` | Design finalization: generates production-quality Pretext-native HTML/CSS. (gstack) |
| `design-review` | Designer's eye QA: finds visual inconsistency, spacing issues, hierarchy problems, AI slop patterns, and slow interactions — then fixes them. (gstack) |
| `design-shotgun` | Design shotgun: generate multiple AI design variants, open a comparison board, collect structured feedback, and iterate. (gstack) |
| `devex-review` | Live developer experience audit. (gstack) |
| `diagram` | Turn an English description (or mermaid source) into a diagram triplet: the source, an editable .excalidraw file you can open on excalidraw.com, and rendered SVG + PNG. (gstack) |
| `document-generate` | Generate missing documentation from scratch for a feature, module, or entire project. (gstack) |
| `document-release` | Post-ship documentation update. (gstack) |
| `freeze` | Restrict file edits to a specific directory for the session. (gstack) |
| `gstack-upgrade` | 升级 gstack 平台与相关组件 |
| `guard` | Full safety mode: destructive command warnings + directory-scoped edits. (gstack) |
| `health` | Code quality dashboard. (gstack) |
| `investigate` | Systematic debugging with root cause investigation. (gstack) |
| `land-and-deploy` | Land and deploy workflow. (gstack) |
| `landing-report` | Read-only queue dashboard for workspace-aware ship. (gstack) |
| `learn` | Manage project learnings. |
| `make-pdf` | Turn any markdown file into a publication-quality PDF. (gstack) |
| `office-hours` | YC Office Hours — two modes. (gstack) |
| `open-gstack-browser` | Launch GStack Browser — AI-controlled Chromium with the sidebar extension baked in. |
| `pair-agent` | Pair a remote AI agent with your browser. (gstack) |
| `plan-ceo-review` | CEO/founder-mode plan review. (gstack) |
| `plan-design-review` | Designer's eye plan review — interactive, like CEO and Eng review. (gstack) |
| `plan-devex-review` | Interactive developer experience plan review. (gstack) |
| `plan-eng-review` | Eng manager-mode plan review. (gstack) |
| `plan-tune` | Self-tuning question sensitivity + developer psychographic for gstack (v1: observational). (gstack) |
| `qa` | Systematically QA test a web application and fix bugs found. (gstack) |
| `qa-only` | Report-only QA testing. (gstack) |
| `retro` | Weekly engineering retrospective. (gstack) |
| `review` | Pre-landing PR review. (gstack) |
| `scrape` | Pull data from a web page. (gstack) |
| `setup-browser-cookies` | Import cookies from your real Chromium browser into the headless browse session. (gstack) |
| `setup-deploy` | Configure deployment settings for /land-and-deploy. |
| `setup-gbrain` | Set up gbrain for this coding agent: install the CLI, initialize a local PGLite or Supabase brain, register MCP, capture per-remote trust policy. (gstack) |
| `ship` | Ship workflow: detect + merge base branch, run tests, review diff, bump VERSION, update CHANGELOG, commit, push, create PR. (gstack) |
| `skillify` | Codify the most recent successful /scrape flow into a permanent browser-skill on disk. (gstack) |
| `spec` | Turn vague intent into a precise, executable spec in five phases. (gstack) |
| `sync-gbrain` | Keep gbrain current with this repo's code and refresh agent search guidance in CLAUDE.md. (gstack) |
| `unfreeze` | Clear the freeze boundary set by /freeze, allowing edits to all directories again. (gstack) |

### 🌐 languages
_各语言规范_

| 技能 | 用途 |
| --- | --- |
| `cpp-testing` | 配置并诊断 GoogleTest 与 CTest 及覆盖率 |

### 🔧 misc
_其他_

| 技能 | 用途 |
| --- | --- |
| `configure-ecc` | 交互式安装 Everything Claude Code 技能与规则 |
| `continuous-learning-v2` | 基于本能观察会话并演化为技能的学习系统 |
| `growth-log` | Use after a complex task, failure, or when reviewing what was learned. Teaches how to write growth logs that extract reusable patterns — not diary entries. |
| `nutrient-document-processing` | 用 Nutrient API 处理转换 OCR 各种文档 |
| `project-guidelines-example` | 基于真实应用的示例项目级技能模板 |
| `search-first` | 写自定义代码前先检索现有工具与库 |
| `security-scan` | 扫描 Claude Code 配置的安全漏洞与注入风险 |
| `skill-stocktake` | 审计 Claude 技能与命令的质量评估流程 |
| `strategic-compact` | 在合理节点手动压缩上下文以保留信息 |
| `verification-loop` | Claude Code 会话的全面验证系统 |

### 🧭 pstack
_poteto 工程方法论_

| 技能 | 用途 |
| --- | --- |
| `architect` | 先勾勒类型与模块结构再进入实现 |
| `arena` | 并行生成多个候选方案并融合最优部分 |
| `automate-me` | 把个人工作偏好沉淀为 -mode 技能 |
| `blast-radius` | 找出改动上线前可能破坏的其他部分 |
| `bro` | 用无行话的通俗语言复述上一条消息 |
| `create-verification-skill` | 生成驱动应用的项目级验证技能 |
| `figure-it-out` | 为大型迁移设计可审计的执行剧本 |
| `how` | 讲解代码如何运作与各层归属 |
| `interrogate` | 多模型从独立角度挑战代码并寻找盲点 |
| `maintain-verification-skill` | 定期审计并保持项目验证技能与特性映射准确 |
| `no-comments` | 处理代码注释问题并修复被接受的意见 |
| `poteto-mode` | 以简洁详细且可验证的风格执行任务 |
| `recall` | 从历史与记录重建近期工作状态并给出简报 |
| `reflect` | 并行审查会话并提炼经验落到技能编辑 |
| `setup-pstack` | 按角色配置 pstack 使用的模型 |
| `show-me-your-work` | 用 TSV 日志保留可审阅的决策轨迹 |
| `swarm` | 并行派出多个工作者并汇总为一份报告 |
| `tdd` | 用户明确要求 TDD 或回归测试时才使用 |
| `teach` | 把复杂工作讲得让人真正理解 |
| `technical-writing` | 符合作者文档风格的分层技术写作标准 |
| `typescript-best-practices` | 读写 TS 与 TSX 文件时的最佳实践 |
| `unslop` | 从任何写作中去掉 AI 腔调并随时应用 |
| `why` | 解释为何这样设计并查询证据得出结论 |

### 🔧 refactoring
_重构实践_

| 技能 | 用途 |
| --- | --- |
| `ai-slop-cleaner` | Clean AI-generated code slop with a regression-safe, deletion-first workflow and optional reviewer-only mode |
| `entropy-reduction` | 设计边界清晰且低复杂度的模块化代码 |

### 📦 security

| 技能 | 用途 |
| --- | --- |
| `security-review` | Use this skill when adding authentication, handling user input, working with secrets, creating API endpoints, or implementing payment/sensitive features. Provides comprehensive security checklist and patterns. |

### 📦 spec-kit
_Spec Kit 需求规范与工单套件_

| 技能 | 用途 |
| --- | --- |
| `speckit-agent-context-update` | Refresh the managed Spec Kit section in coding agent context file(s) |
| `speckit-analyze` | Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation. |
| `speckit-chain` | 一键串行执行 spec-kit 完整开发工作流：constitution → specify → [clarify] → plan → [validate] → tasks → [analyze] → implement。 严格按照官方 spec-kit 方法论串联 5 个核心命令 + 3 个官方推荐的质量门禁。 触发词：全流程开发、全程开发、speckit 全流程、串行执行 speckit、用 spec kit 走完整套流程、帮我实现一个功能并用 speckit。 非单步调试场景——如果用户只想执行其中某一步，应使用对应的独立技能而非本 chain skill。 |
| `speckit-checklist` | Generate a custom checklist for the current feature based on user requirements. |
| `speckit-clarify` | Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec. |
| `speckit-constitution` | Create or update the project constitution from interactive or provided principle inputs. |
| `speckit-converge` | Assess the current codebase against the feature's spec, plan, and tasks, then append any remaining unbuilt work as new tasks to tasks.md so implement can complete it. |
| `speckit-git-commit` | Auto-commit changes after a Spec Kit command completes |
| `speckit-git-feature` | Create a feature branch with sequential or timestamp numbering |
| `speckit-git-initialize` | Initialize a Git repository with an initial commit |
| `speckit-git-remote` | Detect Git remote URL for GitHub integration |
| `speckit-git-validate` | Validate current branch follows feature branch naming conventions |
| `speckit-implement` | Execute the implementation plan by processing and executing all tasks defined in tasks.md |
| `speckit-plan` | Execute the implementation planning workflow using the plan template to generate design artifacts. |
| `speckit-specify` | Create or update the feature specification from a natural language feature description. |
| `speckit-tasks` | Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts. |
| `speckit-taskstoissues` | Convert existing tasks into actionable, dependency-ordered GitHub issues for the feature based on available design artifacts. |

### 🧪 testing
_测试_

| 技能 | 用途 |
| --- | --- |
| `e2e-testing` | Playwright 端到端测试与页面对象模型实践 |
| `eval-harness` | 实现评估驱动开发的正式评估框架 |

### 🔌 tools
_工具集成_

| 技能 | 用途 |
| --- | --- |
| `doc` | 用 python-docx 读取、创建与编辑 docx 文档 |
| `generating-python-installer` | Commercial-grade Python installer expert for Windows: Nuitka extreme compilation, dist slimming, DLL footprint analysis, and Inno Setup packaging to ship the smallest, fastest installers. Use when a Python app must ship as a minimal, fast-starting Windows installer; not for basic script-to-exe conversion. 中文触发：Nuitka 极限优化、Python 商业打包、极限编译 Python、dist 瘦身、DLL 分析、最小安装包、最快启动、商业级打包风格 |
| `hud` | Configure HUD display options (layout, presets, display elements) |
| `mcp-setup` | Configure popular MCP servers for enhanced agent capabilities |
| `pdf` | 读取、创建与审查 PDF 并做视觉校验 |
| `playwright` | 从终端自动化真实浏览器进行 UI 测试 |

### 🎨 ui-ux
_前端设计_

| 技能 | 用途 |
| --- | --- |
| `frontend-design` | 打造高质量且有辨识度的前端界面 |
| `motion-patterns` | Production-ready animation patterns for React / Next.js — button, modal, toast, stagger, page transitions, exit animations, scroll, and layout — built on motion-foundations tokens and springs. Use when animating a specific UI element in React or Next.js — button, modal, toast, stagger, page transition, or scroll. |
| `snapping-ui-to-grid` | Use when building, modifying, or reviewing any page-level UI layout — list pages, form pages, dashboards, drawers, or modal content. Triggers include new page scaffolds, UI/UX polish passes, review comments about misaligned edges, uneven toolbar control heights, ragged number columns, misplaced primary buttons, or arbitrary spacing values. |
| `ui-ux-pro-max` | 覆盖多风格多栈的 UI/UX 设计智能库 |

### 📋 workflow
_开发流程_

| 技能 | 用途 |
| --- | --- |
| `blueprint-driven-development` | 按飞书产品蓝图逐小节实现标讯功能 |
| `blueprint-e2e` | 针对飞书产品蓝图的每一个小节（小节粒度，如 4.2.1、4.3.2），独立编写和执行 Playwright E2E 测试， 验证功能实现是否符合蓝图需求。测试即文档——E2E 测试是对蓝图需求的机器可执行描述。 触发场景：用户提到"E2E 测试蓝图书"、"做蓝图的 E2E"、"测试某小节"、"e2e 覆盖"、"推进 E2E"、 "验证蓝图测试覆盖"、"blueprint E2E"、"蓝图书 e2e"、"补充测试覆盖"、"测试即文档"。 与 blueprint-driven-development 的区别：后者负责"实现"功能，本技能负责"验证"实现是否符合蓝图。 核心原则：每个蓝图小节必须有对应 E2E spec，不存在 = 未完成。 含测试覆盖缺口检测、Playwright 脚本自动生成辅助、CI 门禁绑定。 |
| `brainstorming` | 创造性工作前探索用户意图、需求与设计 |
| `create-migration` | 创建 Flyway 数据库迁移脚本（MySQL 8.0），自动检测下一版本号、生成迁移 SQL 和回滚脚本、执行格式校验。当检测到新增或修改数据库表结构需求时自动触发。 |
| `dispatching-parallel-agents` | 并行派发相互独立的任务给多个代理 |
| `executing-plans` | 在独立会话按检查点执行书面实现计划 |
| `finishing-a-development-branch` | Use when implementation is complete, all tests pass, and you need to decide how to integrate the work |
| `github-sync` | GitHub 与 Gitee 双向代码同步技能（西域数智化投标管理平台）。用于 AI Coding 工具（Cursor/Codex/Claude 等）在 GitHub 远端改代码后同步回本地 Gitee 主仓库，或反向推送本地代码到 GitHub 供 AI 工具使用。触发场景：用户提到"同步 GitHub"、"拉取 AI 改动"、"GitHub 代码合回 Gitee"、"推 GitHub 镜像"、"AI Cursor 改的代码怎么拉回来"、"github-sync"、"同步远端 AI 改动"。 |
| `google-code-review` | 执行 Google 风格的代码审查流程 |
| `html-first-workflow` | 以 HTML 优先的工作流开发前端 |
| `knowledge-capture` | 将 session 中的开发/改 bug/架构/需求确认结果按类型沉淀到 docs/。 写 docs/ 不写 .wiki/，严格遵循现有格式，每条知识有明确归属。 |
| `linear-task-creator` | 创建或更新 Linear 任务并套用项目模板 |
| `llm-knowledge-base` | 构建跨会话累积的 LLM 知识库 |
| `parse-prd` | 解析飞书 PRD 文档：提取正文、画板、截图、HTML 片段和注释，合并为结构化需求简报。当用户提供飞书 PRD 链接时自动触发。 |
| `product-analysis` | 竞品分析、需求优先级与产品文档撰写 |
| `production-risk-review` | 对上线系统 PR 做生产风险审计 |
| `pseo` | 执行产品搜索优化相关的流程 |
| `receiving-code-review` | 收到审查反馈时严谨验证而非盲从 |
| `requesting-code-review` | 完成任务或合并前请求代码审查 |
| `setup` | Use first for install/update routing — sends setup, doctor, or MCP requests to the correct OMC setup flow |
| `six-step-finish` | 通用六步任务收尾：知识沉淀、Wiki 检查、合并确认（可选 forge）、锚点同步、分支核对与卫生清理 |
| `standard-workflow` | 四阶段标准作业流程规划开发质检维护 |
| `subagent-driven-development` | 用子代理执行相互独立的实现计划 |
| `ultrawork` | Parallel execution engine for high-throughput task completion |
| `unified-dev-flow` | 当开始非简单的功能开发、修 bug、重构或迁移，需要决定走哪些阶段、调用哪些技能、走多深时使用。当用户问该用什么流程或技能时使用。触发词：统一流程 / 标准流程 / 开发流程 / 完整流程 / 走流程 / 端到端开发 / 该用什么技能 / 帮我选流程 / 怎么推进这个需求 / 规范流程。Use when deciding which dev workflow/skills to use for a non-trivial coding task. |
| `using-git-worktrees` | 用 git worktree 创建隔离的开发工作区 |
| `verification-before-completion` | 声明完成前先运行验证命令并确认结果 |
| `wiki` | LLM Wiki — persistent markdown knowledge base that compounds across sessions (Karpathy model) |
| `writing-plans` | 动代码前为多步任务编写实现计划 |
| `writing-skills` | 创建、编辑并在部署前验证技能 |
| `xiyu-code-review` | 按西域投标平台规范审查 PR 的架构与安全 |
| `xiyu-mode` | 西域投标管理平台专属模式（质疑复用优先+SpecKit流程+FP-Java+多Agent收尾） |
---

## How to Use a Skill

When the user references a skill by name:
1. Read `~/universal-skills/categories/<category>/<skill-name>/SKILL.md`
2. Follow its instructions as if they were part of your system prompt
3. If the skill references scripts in `scripts/` or data in `data/`, load them as needed

If you are unsure which category a skill is in, search:
```bash
find ~/universal-skills/categories -name "SKILL.md" | xargs grep -l "name: <skill-name>"
```
