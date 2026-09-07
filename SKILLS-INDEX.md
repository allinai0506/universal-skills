# SKILLS-INDEX

> 技能来源速查表 · 自动生成于 2026-09-07 12:25 · 共 353 个一级技能。
> 按「来源」检索：公开技能包（外部大神编写的成套技能） / 自建・单个技能。
> 技能由 AI 按 description 自动触发，无需记住名字。

按来源检索：
[一、公开技能包](#一公开技能包) · [二、自建・单个技能](#二自建单个技能)

## 一、公开技能包
_外部技术大神编写的成套技能，每个包内部技能有使用逻辑。_

### anthropics 官方工具
_安装能力 / 文档 / PDF / 浏览器工具_

**.system** _(元工具（创建 / 安装技能）)_

| 技能 | 用途 |
| --- | --- |
| `skill-creator` | 创建或更新 AI 技能文件夹以扩展工具能力 |
| `skill-installer` | 从列表或 GitHub 仓库安装技能到本地工具目录 |

**tools** _(工具集成)_

| 技能 | 用途 |
| --- | --- |
| `doc` | 用 python-docx 读取、创建与编辑 docx 文档 |
| `pdf` | 读取、创建与审查 PDF 并做视觉校验 |
| `playwright` | 从终端自动化真实浏览器进行 UI 测试 |

### gstack 发行版
_Everything Claude Code 全家桶定制技能_

**gstack** _(gstack 发行版定制技能)_

| 技能 | 用途 |
| --- | --- |
| `autoplan` | Auto-review pipeline — reads the full CEO, design, eng, and DX review skills from disk and runs them sequentially with auto-decisions using 6 decision principles. (gstack) |
| `benchmark` | Performance regression detection using the browse daemon. (gstack) |
| `benchmark-models` | Cross-model benchmark for gstack skills. (gstack) |
| `browse` | Fast headless browser for QA testing and site dogfooding. (gstack) |
| `canary` | Post-deploy canary monitoring. (gstack) |
| `careful` | Safety guardrails for destructive commands. (gstack) |
| `codex` | OpenAI Codex CLI wrapper — three modes. (gstack) |
| `connect-chrome` | Launch GStack Browser — AI-controlled Chromium with the sidebar extension baked in. |
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
| `ios-clean` | Remove the DebugBridge SPM package and all #if DEBUG wiring from an iOS app. (gstack) |
| `ios-design-review` | Visual design audit for iOS apps on real hardware. (gstack) |
| `ios-fix` | Autonomous iOS bug fixer. (gstack) |
| `ios-qa` | Live-device iOS QA for SwiftUI apps. (gstack) |
| `ios-sync` | Regenerate the iOS debug bridge against the latest upstream gstack templates. (gstack) |
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

### mattpocock / skills
_需求→规格→工单→实现→验证的完整工程闭环_

**engineering** _(mattpocock 工程技能)_

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

### poteto 工程方法论
_poteto-mode 工作流 + 21 条工程原则_

**pstack** _(poteto 工程方法论)_

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
| `principle-boundary-discipline` | 把校验与错误处理集中在系统边界 |
| `principle-build-the-lever` | 为重复性工作构建可复跑的工具而非手工操作 |
| `principle-encode-lessons-in-structure` | 把重复指导编码为检查或脚本而非文字 |
| `principle-exhaust-the-design-space` | 面对新交互时构建多个原型对比后再定案 |
| `principle-experience-first` | 优先用户愉悦而非实现便利并宁精勿多 |
| `principle-fix-root-causes` | 先复现并追根因避免用零检查掩盖崩溃 |
| `principle-foundational-thinking` | 写逻辑前先定好核心类型与数据结构 |
| `principle-guard-the-context-window` | 把批量内容路由给子代理而主线程只留摘要 |
| `principle-laziness-protocol` | 重构时偏向删除与最小改动 |
| `principle-make-operations-idempotent` | 让命令与处理在重启重试后收敛到同一终态 |
| `principle-migrate-callers-then-delete-legacy-apis` | 引入新 API 时同步迁移调用方并删除旧 API |
| `principle-minimize-reader-load` | 减少层数与隐藏状态以简化代码追踪 |
| `principle-model-the-domain` | 把领域编码进结构而非散落的条件分支 |
| `principle-never-block-on-the-human` | 可逆工作先推进再让人纠偏仅不可逆需确认 |
| `principle-outcome-oriented-execution` | 迁移时收敛目标架构不保留过渡兼容代码 |
| `principle-prove-it-works` | 完成前对真实产物验证而非自述或编译通过 |
| `principle-redesign-from-first-principles` | 把新需求当作第一天就有的假设来重设计 |
| `principle-separate-before-serializing-shared-state` | 并发写入前先消除共享必要时才结构串行 |
| `principle-sequence-verifiable-units` | 把多步工作拆成可验证的小单元逐步推进 |
| `principle-subtract-before-you-add` | 先删除冗余再在更简单的基础上构建 |
| `principle-type-system-discipline` | 让非法状态不可表示并坚守类型系统 |
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

### 前端设计
_前端界面设计技能_

**ui-ux** _(前端设计)_

| 技能 | 用途 |
| --- | --- |
| `frontend-design` | 打造高质量且有辨识度的前端界面 |
| `snapping-ui-to-grid` | Use when building, modifying, or reviewing any page-level UI layout — list pages, form pages, dashboards, drawers, or modal content. Triggers include new page scaffolds, UI/UX polish passes, review comments about misaligned edges, uneven toolbar control heights, ragged number columns, misplaced primary buttons, or arbitrary spacing values. |
| `ui-ux-pro-max` | 覆盖多风格多栈的 UI/UX 设计智能库 |

---

## 二、自建・单个技能
_自己创建或单独引入的技能，按原分类组织。_

### architecture
_架构模式_

| 技能 | 用途 |
| --- | --- |
| `access-pattern-driven-data-modeling` | 依据访问模式设计数据库表、索引与查询路径 |
| `architecture-defense` | 自动拦截错误依赖与分层违规以守护架构边界 |
| `cog-4d-audit` | 对已通过 CI 的代码做四维深度审查揪出隐藏缺陷 |

### coding
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

### data
_数据 / 数据库模式_

| 技能 | 用途 |
| --- | --- |
| `clickhouse-io` | ClickHouse 查询优化与高性能分析数据工程实践 |
| `postgres-patterns` | PostgreSQL 查询优化、表设计、索引与安全实践 |

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
| `docker-patterns` | Docker 与 Compose 的开发、安全与多服务编排模式 |
| `xiyu-server-deploy` | 西域投标平台服务器部署、健康检查与回滚预案 |

### imported
_自动发现的第三方技能_

| 技能 | 用途 |
| --- | --- |
| `_gstack-command` | Router for the gstack skill suite. (gstack) |
| `accessibility` | Design, implement, and audit inclusive digital products using WCAG 2.2 Level AA. Use when building or auditing UI that must meet WCAG 2.2 Level AA, or when reviewing a change for keyboard, contrast, or screen-reader support. |
| `agent-introspection-debugging` | Structured self-debugging workflow for AI agent failures using capture, diagnosis, contained recovery, and introspection reports. Use when an agent run fails and you need a reproducible diagnosis instead of a retry. |
| `agent-self-evaluation` | Use after completing any non-trivial task. The agent self-rates its output on 5 axes — accuracy, completeness, clarity, actionability, conciseness — with concrete evidence per criterion. Produces a structured 1-5 scorecard with specific improvement suggestions. |
| `agent-sort` | Build an evidence-backed ECC install plan for a specific repo by sorting skills, commands, rules, hooks, and extras into DAILY vs LIBRARY buckets using parallel repo-aware review passes. Use when ECC should be trimmed to what a project actually needs instead of loading the full bundle. |
| `ai-regression-testing` | Regression testing strategies for AI-assisted development. Sandbox-mode API testing without database dependencies, automated bug-check workflows, and patterns to catch AI blind spots where the same model writes and reviews code. Use when adding regression coverage to AI-assisted code, or when the same model both wrote and reviewed a change. |
| `android-clean-architecture` | Clean Architecture patterns for Android and Kotlin Multiplatform projects — module structure, dependency rules, UseCases, Repositories, and data layer patterns. Use when structuring modules, layers, or data flow in an Android or KMP project. |
| `angular-developer` | Generates Angular code and provides architectural guidance. Trigger when creating projects, components, or services, or for best practices on reactivity (signals, linkedSignal, resource), forms, dependency injection, routing, SSR, accessibility (ARIA), animations, styling (component styles, Tailwind CSS), testing, or CLI tooling. |
| `architecture-decision-records` | Capture architectural decisions made during Claude Code sessions as structured ADRs. Auto-detects decision moments, records context, alternatives considered, and rationale. Maintains an ADR log so future developers understand why the codebase is shaped the way it is. |
| `autopilot` | 从想法到可运行代码的全自主执行 |
| `autoresearch` | 带严格评估合约的单任务持续改进循环 |
| `blueprint-e2e` | 为飞书产品蓝图每小节独立编写并执行 E2E 测试 |
| `branch-name` | Use when starting a new branch or renaming an existing one — produces a branch name in the format `<type>/<work-item-id>-<short-description>` that's compatible with the create-pr skill's work item ID extraction. |
| `browser-qa` | Use this skill to automate visual testing and UI interaction verification using browser automation after deploying features. |
| `bun-runtime` | Bun as runtime, package manager, bundler, and test runner. When to choose Bun vs Node, migration notes, and Vercel support. |
| `ck` | Persistent per-project memory for Claude Code. Auto-loads project context on session start, tracks sessions with git activity, and writes to native memory. Commands run deterministic Node.js scripts — behavior is consistent across model versions. Use when a project needs context to survive across Claude Code sessions instead of being re-explained each time. |
| `click-path-audit` | Trace every user-facing button/touchpoint through its full state change sequence to find bugs where functions individually work but cancel each other out, produce wrong final state, or leave the UI in an inconsistent state. Use when: systematic debugging found no bugs but users report broken buttons, or after any major refactor touching shared state stores. |
| `code-tour` | Create CodeTour `.tour` files — persona-targeted, step-by-step walkthroughs with real file and line anchors. Use for onboarding tours, architecture walkthroughs, PR tours, RCA tours, and structured "explain how this works" requests. Use when the user asks for a code tour, onboarding walkthrough, PR tour, or an explanation of how a subsystem works. |
| `codebase-onboarding` | Analyze an unfamiliar codebase and generate a structured onboarding guide with architecture map, key entry points, conventions, and a starter CLAUDE.md. Use when joining a new project or setting up Claude Code for the first time in a repo. |
| `codehealth-mcp` | Real-time structural Code Health via CodeScene MCP — review before edits, verify score deltas after changes, gate commits and PRs. Use when reviewing code quality, refactoring, checking if AI changes degraded a file, or before commit/PR. |
| `compose-multiplatform-patterns` | Compose Multiplatform and Jetpack Compose patterns for KMP projects — state management, navigation, theming, performance, and platform-specific UI. Use when building Compose or Jetpack Compose UI, state, navigation, or theming in a KMP project. |
| `config-gc` | Garbage collection for your Claude Code configuration. Periodically scans ~/.claude (skills, memory, hooks, permissions, MCP servers, caches) for redundant, stale, orphaned, or low-value items, then walks the user through a confirm-each-deletion cleanup. Use when the user says "clean up my config", "config GC", "too many skills", "audit my setup", "my .claude is bloated", or asks for a periodic config review. |
| `configure-notifications` | 用自然语言配置 Telegram、Discord 与 Slack 通知 |
| `context-budget` | Audits Claude Code context window consumption across agents, skills, MCP servers, and rules. Identifies bloat, redundant components, and produces prioritized token-savings recommendations. Use when the context window is filling up too fast and the agents, skills, MCP servers, or rules consuming it need to be identified. |
| `continuous-learning` | [DEPRECATED - use continuous-learning-v2] Legacy v1 stop-hook skill extractor. v2 is a strict superset with instinct-based, project-scoped, hook-reliable learning. Do not invoke v1: when continuous learning, session learning, or pattern extraction is requested, route to continuous-learning-v2 instead. |
| `contract-first` | Use when multiple consumers and providers must evolve an API or event schema without field drift, integration surprises, or one side silently redefining the interface. |
| `council` | Convene a four-voice council for ambiguous decisions, tradeoffs, and go/no-go calls. Use when multiple valid paths exist and you need structured disagreement before choosing. |
| `council-multi-model` | Add one optional external Codex critique after the existing council has produced a decision draft. Use when an ambiguous, high-consequence decision would benefit from a separate model invocation's attempt to break the synthesis. Requires explicit consent before sending the compact draft and disagreement to OpenAI, labels same-provider reviews honestly, and marks the review absent when the adapter is unavailable. |
| `cpp-coding-standards` | C++ coding standards based on the C++ Core Guidelines (isocpp.github.io). Use when writing, reviewing, or refactoring C++ code to enforce modern, safe, and idiomatic practices. |
| `create-migration` | 生成 Flyway 迁移脚本并做格式校验 |
| `create-pull-request` | Use when creating a pull request for the current branch — gathers branch context, generates a PR description following the repo's pull_request_template.md, and creates the PR with a Plane work item ID prefix in the title. |
| `csharp-testing` | C# and .NET testing patterns with xUnit, FluentAssertions, mocking, integration tests, and test organization best practices. Use when writing or reviewing xUnit tests, mocks, or integration tests in a C# / .NET project. |
| `dart-flutter-patterns` | Production-ready Dart and Flutter patterns covering null safety, immutable state, async composition, widget architecture, popular state management frameworks (BLoC, Riverpod, Provider), GoRouter navigation, Dio networking, Freezed code generation, and clean architecture. Use when writing or reviewing Dart and Flutter code — state, widgets, navigation, networking, or architecture. |
| `deep-dive` | 两阶段管线做因果追踪与需求澄清的深度调查 |
| `deep-interview` | 苏格拉底式深度访谈并澄清需求中的数学歧义 |
| `deepinit` | 用分层 AGENTS.md 文档深度初始化代码库 |
| `delivery-gate` | Stop hook that blocks Claude from finishing until quality checks pass. Detects rationalization patterns (surface text heuristics), stale learning logs (filesystem mtime), and low disk space. Complements self-audit by mechanically enforcing learning capture habits. Use when Claude should be mechanically blocked from declaring work finished before quality checks and learning capture actually pass. |
| `design-system` | Use this skill to generate or audit design systems, check visual consistency, and review PRs that touch styling. Use when generating or auditing a design system, checking visual consistency, or reviewing a PR that touches styling. |
| `dev-team` | Simulate a collaborative dev team session where multiple role-based personas (PM, Architect, Developer, QA) respond to the same problem together in one session. Use when designing a feature, reviewing a proposal, or onboarding a new initiative and you want multi-role perspective without switching agents manually. |
| `django-celery` | Django + Celery async task patterns — configuration, task design, beat scheduling, retries, canvas workflows, monitoring, and testing. Use when adding background jobs, scheduled tasks, or async processing to a Django app. |
| `django-patterns` | Django architecture patterns, REST API design with DRF, ORM best practices, caching, signals, middleware, and production-grade Django apps. Use when building or reviewing Django apps, DRF APIs, ORM queries, or caching. |
| `django-tdd` | Django testing strategies with pytest-django, TDD methodology, factory_boy, mocking, coverage, and testing Django REST Framework APIs. Use when writing Django or DRF tests with pytest-django, or driving a Django feature test-first. |
| `django-verification` | Verification loop for Django projects: migrations, linting, tests with coverage, security scans, and deployment readiness checks before release or PR. |
| `dmux-workflows` | Multi-agent orchestration using dmux (tmux pane manager for AI agents). Patterns for parallel agent workflows across Claude Code, Codex, OpenCode, and other harnesses. Use when running multiple agent sessions in parallel or coordinating multi-agent development workflows. |
| `dotnet-patterns` | Idiomatic C# and .NET patterns, conventions, dependency injection, async/await, and best practices for building robust, maintainable .NET applications. Use when writing or reviewing C# / .NET code — DI, async, or general conventions. |
| `ecc-guide` | Guide users through ECC's current agents, skills, commands, hooks, rules, install profiles, and project onboarding by reading the live repository surface before answering. |
| `ecc-recipes` | Map a described workflow to the right ECC command-GROUP with run-order and stop condition, and browse all command-group recipe families. Adds a family-grouping + run-order + when-to-stop layer on top of the flat command catalog. Advisory only. TRIGGER when the user says which commands for X, what command group runs X, show ECC recipes, list ECC pipelines, or how do I run a workflow with ECC. DO NOT TRIGGER when the user wants the task executed directly, wants a single-command deep doc (use ecc-guide), or wants a draft prompt rewritten (use prompt-optimizer). |
| `error-handling` | Patterns for robust error handling across TypeScript, Python, and Go. Covers typed errors, error boundaries, retries, circuit breakers, and user-facing error messages. Use when designing error types, retries, circuit breakers, or user-facing failure messages in TypeScript, Python, or Go. |
| `external-context` | 并行调用文档专家代理做外部检索与查询 |
| `fastapi-patterns` | FastAPI best practices covering project structure, Pydantic v2 schemas, dependency injection, async handlers, authentication, authorization, transactional service layers, and testing with httpx and pytest. Use when building or reviewing FastAPI apps — Pydantic schemas, dependencies, async handlers, auth, or tests. |
| `flutter-dart-code-review` | Library-agnostic Flutter/Dart code review checklist covering widget best practices, state management patterns (BLoC, Riverpod, Provider, GetX, MobX, Signals), Dart idioms, performance, accessibility, security, and clean architecture. Use when reviewing Flutter or Dart code, whatever state management library the project uses. |
| `frontend-a11y` | Accessibility patterns for React and Next.js — semantic HTML, ARIA attributes, form labeling, keyboard navigation, focus management, and screen reader support. Use when building any interactive UI component or form. |
| `frontend-design-direction` | Set an ECC-specific frontend design direction for production UI work. Use when building or improving websites, dashboards, applications, components, landing pages, visual tools, or any web UI that needs stronger product-specific design judgment. |
| `frontend-slides` | Create stunning, animation-rich HTML presentations from scratch or by converting PowerPoint files. Use when the user wants to build a presentation, convert a PPT/PPTX to web, or create slides for a talk/pitch. Helps non-designers discover their aesthetic through visual exploration rather than abstract choices. |
| `fsharp-testing` | F# testing patterns with xUnit, FsUnit, Unquote, FsCheck property-based testing, integration tests, and test organization best practices. Use when writing F# tests with xUnit, FsUnit, Unquote, or FsCheck. |
| `generating-python-installer` | Commercial-grade Python installer expert for Windows: Nuitka extreme compilation, dist slimming, DLL footprint analysis, and Inno Setup packaging to ship the smallest, fastest installers. Use when a Python app must ship as a minimal, fast-starting Windows installer; not for basic script-to-exe conversion. 中文触发：Nuitka 极限优化、Python 商业打包、极限编译 Python、dist 瘦身、DLL 分析、最小安装包、最快启动、商业级打包风格 |
| `git-workflow` | Git workflow patterns including branching strategies, commit conventions, merge vs rebase, conflict resolution, and collaborative development best practices for teams of all sizes. Use when choosing a branching strategy, writing commit conventions, deciding merge versus rebase, or resolving conflicts. |
| `github-sync` | 在 GitHub 与 Gitee 之间双向同步西域项目代码 |
| `golang-patterns` | Idiomatic Go patterns, best practices, and conventions for building robust, efficient, and maintainable Go applications. Use when writing or reviewing Go code and idiomatic structure or conventions are in question. |
| `golang-testing` | Go testing patterns including table-driven tests, subtests, benchmarks, fuzzing, and test coverage. Follows TDD methodology with idiomatic Go practices. Use when writing Go tests — table-driven cases, subtests, benchmarks, fuzzing, or coverage. |
| `growth-log` | Use after a complex task, failure, or when reviewing what was learned. Teaches how to write growth logs that extract reusable patterns — not diary entries. |
| `gstack` | Router for the gstack skill suite. (gstack) |
| `gstack-codex` | OpenAI Codex CLI wrapper — three modes. (gstack) |
| `gstack-connect-chrome` | Launch GStack Browser — AI-controlled Chromium with the sidebar extension baked in. |
| `gstack-gstack-upgrade` | Upgrade gstack to the latest version. |
| `hexagonal-architecture` | Design, implement, and refactor Ports & Adapters systems with clear domain boundaries, dependency inversion, and testable use-case orchestration across TypeScript, Java, Kotlin, and Go services. Use when introducing or refactoring toward Ports and Adapters, or when domain logic has become entangled with I/O. |
| `hookify-rules` | This skill should be used when the user asks to create a hookify rule, write a hook rule, configure hookify, add a hookify rule, or needs guidance on hookify rule syntax and patterns. |
| `hud` | 配置 HUD 显示布局、预设与元素 |
| `impeccable` | 全面设计、审查并打磨各种前端界面 |
| `inherit-legacy-style` | Legacy-project style inheritance skill. Use when the user types /inherit-legacy-style, or when onboarding an AI coding agent onto a hand-written legacy project and you need to prevent "style drift" (the model imposing its pretrained mainstream idioms onto the project). Language- and framework-agnostic — it aligns meta-architecture only, not syntax. Once run, it becomes a behavioral constraint on all subsequent coding tasks. Do NOT use for pure research or one-off questions unrelated to code-style alignment. |
| `intent-driven-development` | Turn ambiguous or high-impact product and engineering changes into scoped, verifiable acceptance criteria before or alongside implementation. Use when a user asks to clarify a feature, define acceptance criteria, de-risk a security/data/migration/integration change, prepare implementation requirements for another agent, or make a complex request testable. Do not trigger for trivial edits, straightforward fixes, active debugging, code review, or implementation requests whose acceptance conditions are already clear unless the user explicitly invokes this skill. |
| `iterative-retrieval` | Pattern for progressively refining context retrieval to solve the subagent context problem. Use when a subagent lacks the context it needs and retrieval must be refined across passes. |
| `java-coding-standards` | Java coding standards for Spring Boot and Quarkus services: naming, immutability, Optional usage, streams, exceptions, generics, CDI, reactive patterns, and project layout. Automatically applies framework-specific conventions. Use when writing or reviewing Java in a Spring Boot or Quarkus service. |
| `jpa-patterns` | JPA/Hibernate patterns for entity design, relationships, query optimization, transactions, auditing, indexing, pagination, and pooling in Spring Boot. Use when designing JPA entities or relationships, or when a Hibernate query, transaction, or N+1 problem needs fixing. |
| `knowledge-capture` | 捕获并沉淀开发过程中的知识与经验 |
| `kotlin-coroutines-flows` | Kotlin Coroutines and Flow patterns for Android and KMP — structured concurrency, Flow operators, StateFlow, error handling, and testing. Use when writing coroutines or Flow code on Android or KMP, or debugging cancellation and concurrency. |
| `kotlin-exposed-patterns` | JetBrains Exposed ORM patterns including DSL queries, DAO pattern, transactions, HikariCP connection pooling, Flyway migrations, and repository pattern. Use when working with the Exposed ORM — DSL or DAO queries, transactions, pooling, or migrations. |
| `kotlin-ktor-patterns` | Ktor server patterns including routing DSL, plugins, authentication, Koin DI, kotlinx.serialization, WebSockets, and testApplication testing. Use when building a Ktor server — routing, plugins, auth, DI, serialization, or tests. |
| `kotlin-patterns` | Idiomatic Kotlin patterns, best practices, and conventions for building robust, efficient, and maintainable Kotlin applications with coroutines, null safety, and DSL builders. Use when writing or reviewing Kotlin code and idiomatic structure or null safety is in question. |
| `kotlin-testing` | Kotlin testing patterns with Kotest, MockK, coroutine testing, property-based testing, and Kover coverage. Follows TDD methodology with idiomatic Kotlin practices. Use when writing Kotlin tests with Kotest or MockK, or testing coroutines and checking coverage. |
| `laravel-patterns` | Laravel architecture patterns, routing/controllers, Eloquent ORM, service layers, queues, events, caching, and API resources for production apps. Use when building or reviewing Laravel apps — controllers, Eloquent, service layers, queues, or API resources. |
| `laravel-plugin-discovery` | Discover and evaluate Laravel packages via LaraPlugins.io MCP. Use when the user wants to find plugins, check package health, or assess Laravel/PHP compatibility. |
| `laravel-tdd` | Laravel testing strategies with PHPUnit, Pest, model factories, HTTP tests, Sanctum authentication testing, mocking, and coverage. Use when writing Laravel tests with PHPUnit or Pest, or driving a Laravel feature test-first. |
| `laravel-verification` | Verification loop for Laravel projects: env checks, linting, static analysis, tests with coverage, security scans, and deployment readiness. Use when verifying a Laravel project before merge or deploy — lint, static analysis, tests, coverage, security. |
| `learner` | 从当前对话中提炼可复用的技能 |
| `living-docs-governance` | Keep a long-lived project's documentation from rotting by assigning existing project docs clear constitution, map, status, and history roles, then wiring the active agent harness to those canonical sources. Use in the maintain phase when docs drift from code, agents lose context between sessions, or intentional removals keep being recreated. Prefer adopting the repository's current docs structure over creating new root files. 中文触发：文档治理、活文档、项目状态追踪、防文档漂移、项目地图、健康仪表盘、删除区、长期项目治理 |
| `loop-design-check` | Design a goal-oriented agent loop, and review it for the ways loops go wrong — spinning and burning tokens, Goodhart-gaming the verifier, or running a wrong answer to completion. Two actions: (1) WRITE a loop — gate whether to build it, define a machine-decidable goal, pick the loop type, pick a skeleton; (2) REVIEW a loop — run it past five failure modes plus decidability, boundaries, fallback, judge independence, and keep-judgment-with-the-human red lines. Use when designing an autonomous agent loop, or when you already have one and worry it will spin, cheat, or run a wrong answer to the end. Complements the mechanism-layer loop skills (autonomous-loops, continuous-agent-loop) by covering the judgment layer they don't. 中文触发：写 loop、设计 loop、做一个 loop、检查 loop 对不对、loop 体检、loop 会不会跑飞、可判定目标、五个崩法、plan build judge。English triggers: design an agent loop, write a loop, check a loop, loop review, prevent a runaway loop, goal-oriented loop, decidable goal, plan/build/judge. |
| `make-interfaces-feel-better` | Apply concrete design-engineering details that make interfaces feel polished. Use when reviewing or improving UI spacing, typography, borders, shadows, motion, hit areas, icons, text wrapping, and interaction states. |
| `mcp-server-patterns` | Build MCP servers with Node/TypeScript SDK — tools, resources, prompts, Zod validation, stdio vs Streamable HTTP. Use Context7 or official MCP docs for latest API. Use when building or debugging an MCP server — tools, resources, prompts, validation, or transport choice. |
| `mcp-setup` | 配置常用 MCP 服务器以增强代理能力 |
| `motion-advanced` | Advanced motion patterns for React / Next.js — drag & drop, gestures, text animations, SVG path drawing, custom hooks, imperative sequences (useAnimate), loaders, and the full API decision tree. Requires motion-foundations. Use when building drag and drop, gestures, text or SVG animation, or imperative animation sequences in React or Next.js. |
| `motion-foundations` | Motion tokens, spring presets, performance rules, device adaptation, accessibility enforcement, and SSR safety for React / Next.js using motion/react. Foundation layer — all other motion skills depend on this. Use when setting up motion tokens, spring presets, reduced-motion handling, or SSR-safe animation in React or Next.js. |
| `motion-patterns` | Production-ready animation patterns for React / Next.js — button, modal, toast, stagger, page transitions, exit animations, scroll, and layout — built on motion-foundations tokens and springs. Use when animating a specific UI element in React or Next.js — button, modal, toast, stagger, page transition, or scroll. |
| `motion-ui` | Production-ready UI motion system for React/Next.js. Use when implementing animations, transitions, or motion patterns. |
| `mysql-patterns` | MySQL and MariaDB schema, query, indexing, transaction, replication, and connection-pool patterns for production backends. Use when designing MySQL or MariaDB schemas and indexes, or when a query, transaction, or replica lags. |
| `nestjs-patterns` | NestJS architecture patterns for modules, controllers, providers, DTO validation, guards, interceptors, config, and production-grade TypeScript backends. Use when building or reviewing a NestJS backend — modules, providers, DTO validation, guards, or interceptors. |
| `nextjs-turbopack` | Next.js 16+ and Turbopack — incremental bundling, FS caching, dev speed, and when to use Turbopack vs webpack. |
| `nuxt4-patterns` | Nuxt 4 app patterns for hydration safety, performance, route rules, lazy loading, and SSR-safe data fetching with useFetch and useAsyncData. Use when building or reviewing a Nuxt 4 app, or debugging hydration mismatches and SSR-safe data fetching. |
| `parse-prd` | 解析飞书 PRD 文档为结构化需求简报 |
| `perl-patterns` | Modern Perl 5.36+ idioms, best practices, and conventions for building robust, maintainable Perl applications. Use when writing or reviewing modern Perl 5.36+ code. |
| `perl-testing` | Perl testing patterns using Test2::V0, Test::More, prove runner, mocking, coverage with Devel::Cover, and TDD methodology. Use when writing Perl tests with Test2::V0 or Test::More, or measuring coverage. |
| `plan-canvas` | Open plans and HTML artifacts in a local browser canvas where the human annotates elements, chats, and approves or requests changes without leaving the page. Use when presenting a plan for review, or when feedback like "move this, change that" is easier pointed at than typed. |
| `plankton-code-quality` | Write-time code quality enforcement using Plankton — auto-formatting, linting, and Claude-powered fixes on every file edit via hooks. Use when setting up write-time formatting, linting, or auto-fix hooks on file edits. |
| `prisma-patterns` | Prisma ORM patterns for TypeScript backends — schema design, query optimization, transactions, pagination, and critical traps like updateMany returning count not records, $transaction timeouts, migrate dev resetting the DB, @updatedAt skipped on bulk writes, and serverless connection exhaustion. Use when writing a Prisma schema or query, or debugging transactions, migrations, or serverless connection limits. |
| `product-lens` | Use this skill to validate the "why" before building, run product diagnostics, and pressure-test product direction before the request becomes an implementation contract. |
| `production-audit` | Local-evidence production readiness audit for shipped apps, pre-launch reviews, post-merge checks, and "what breaks in prod?" questions without sending repo data to an external audit service. Use when auditing production readiness before launch, after a merge, or when asked what breaks in prod. |
| `project-session-manager` | 以工作树优先管理开发环境与工单会话 |
| `python-patterns` | Pythonic idioms, PEP 8 standards, type hints, and best practices for building robust, efficient, and maintainable Python applications. Use when writing or reviewing Python code and idiomatic structure, typing, or PEP 8 is in question. |
| `python-testing` | Python testing strategies using pytest, TDD methodology, fixtures, mocking, parametrization, and coverage requirements. Use when writing pytest tests — fixtures, mocks, parametrization, or coverage. |
| `quarkus-patterns` | Quarkus 3.x LTS architecture patterns with Camel for messaging, RESTful API design, CDI services, data access with Panache, and async processing. Use for Java Quarkus backend work with event-driven architectures. Use when building or reviewing a Quarkus service, especially with Camel messaging or Panache data access. |
| `quarkus-tdd` | Test-driven development for Quarkus 3.x LTS using JUnit 5, Mockito, REST Assured, Camel testing, and JaCoCo. Use when adding features, fixing bugs, or refactoring event-driven services. |
| `quarkus-verification` | Verification loop for Quarkus projects: build, static analysis, tests with coverage, security scans, native compilation, and diff review before release or PR. |
| `ralph` | 带可配置验证评审的自循环任务执行 |
| `ralplan` | 执行前对模糊请求做共识规划的入口 |
| `react-doctor` | Use when finishing a feature, fixing a bug, before committing React code, or when the user types `/doctor`, asks to scan, triage, or clean up React diagnostics. Covers lint, accessibility, bundle size, architecture. Includes a regression check and a full local-triage workflow that fetches the canonical playbook. |
| `react-native-patterns` | React Native and Expo app patterns — Expo Router navigation, state separation (server/client/route/form), TanStack Query data fetching with Zod, performant lists, NativeWind/StyleSheet styling, native APIs, and secure storage. Use when building or editing React Native / Expo screens, components, navigation, or data layers. |
| `react-patterns` | React 18/19 patterns including hooks discipline, server/client component boundaries, Suspense + error boundaries, form actions, data fetching, state management decision trees, and accessibility-first composition. Use when writing or reviewing React components. |
| `react-performance` | React and Next.js performance optimization patterns adapted from Vercel Engineering's React Best Practices (https://github.com/vercel-labs/agent-skills). Organizes 70+ rules across 8 priority categories — waterfalls, bundle size, server-side, client fetching, re-render, rendering, JS micro-perf, advanced. Use when writing, reviewing, or refactoring React/Next.js code for performance. |
| `react-testing` | React component testing with React Testing Library, Vitest/Jest, MSW for network mocking, accessibility assertions with axe, and the decision boundary between component tests and Playwright/Cypress end-to-end runs. Use when writing or fixing tests for React components, hooks, or pages. |
| `redis-patterns` | Redis data structure patterns, caching strategies, distributed locks, rate limiting, pub/sub, and connection management for production applications. Use when adding caching, a distributed lock, rate limiting, or pub/sub with Redis, or when key design needs review. |
| `release` | 分析仓库发布规则并引导完成发布流程 |
| `release-notes` | Generate release notes for a Plane release PR in either `makeplane/plane-cloud` (date-based versioning, e.g. `release: vYY.MM.DD-N`) or `makeplane/plane-ee` (semver, e.g. `release: vX.Y.Z`). Reads PR commits, filters out noise, categorizes by conventional-commit type, optionally enriches via Plane MCP, and writes the result as the PR description in the GitHub Releases format. |
| `repo-scan` | Bootstrap pointer that installs the external repo-scan skill from a pinned, reviewable commit. Use when repo-scan must be installed before running its cross-stack source-code asset audit; this ECC pointer does not perform the audit itself. |
| `rules-distill` | Scan skills to extract cross-cutting principles and distill them into rules — append, revise, or create new rule files. Use when the same principle keeps recurring across skills and belongs in a rule file instead. |
| `rust-patterns` | Idiomatic Rust patterns, ownership, error handling, traits, concurrency, and best practices for building safe, performant applications. Use when writing or reviewing Rust code and ownership, error handling, traits, or concurrency is in question. |
| `rust-testing` | Rust testing patterns including unit tests, integration tests, async testing, property-based testing, mocking, and coverage. Follows TDD methodology. Use when writing Rust tests — unit, integration, async, property-based, or coverage. |
| `santa-method` | Multi-agent adversarial verification with convergence loop. Two independent review agents must both pass before output ships. Use when output must clear two independent adversarial reviewers before it ships. |
| `self-improve` | 用锦标赛选择实现代码的自主进化改进 |
| `setup` | 把安装诊断与 MCP 请求路由到正确流程 |
| `skill` | 列出、添加、移除并搜索本地技能 |
| `skill-comply` | Visualize whether skills, rules, and agent definitions are actually followed — auto-generates scenarios at 3 prompt strictness levels, runs agents, classifies behavioral sequences, and reports compliance rates with full tool call timelines. Use when checking whether agents actually follow the skills, rules, and definitions they were given, rather than assuming they do. |
| `skill-scout` | Search existing local, marketplace, GitHub, and web skill sources before creating a new skill. Use when the user wants to create, build, fork, or find a skill for a workflow. |
| `skillify` | 把可复用工作流提炼成可用的 OMC 技能 |
| `speckit-agent-context-update` | 刷新编码代理上下文文件中的 Spec Kit 章节 |
| `speckit-analyze` | 对规格、计划与任务文档做无损一致性分析 |
| `speckit-checklist` | 按需求为当前功能生成自定义检查清单 |
| `speckit-clarify` | 通过定向提问澄清需求中不明确的部分 |
| `speckit-constitution` | 创建或更新项目章程并保持模板同步 |
| `speckit-converge` | Assess the current codebase against the feature's spec, plan, and tasks, then append any remaining unbuilt work as new tasks to tasks.md so implement can complete it. |
| `speckit-git-commit` | 在 Spec Kit 命令完成后自动提交改动 |
| `speckit-git-feature` | 创建带序号或时间戳的功能分支 |
| `speckit-git-initialize` | 初始化 Git 仓库并创建初始提交 |
| `speckit-git-remote` | 检测 Git 远端地址以集成 GitHub |
| `speckit-git-validate` | 校验当前分支是否符合功能分支命名规范 |
| `speckit-implement` | 按任务清单执行并完成功能实现计划 |
| `speckit-plan` | 用计划模板生成设计产物并执行规划 |
| `speckit-specify` | 从自然语言功能描述创建或更新规格 |
| `speckit-tasks` | 根据设计产物生成有序可执行的任务清单 |
| `speckit-taskstoissues` | 把任务转换为有序的 GitHub 议题 |
| `springboot-patterns` | Spring Boot architecture patterns, REST API design, layered services, data access, caching, async processing, and logging. Use for Java Spring Boot backend work. Use when building or reviewing a Spring Boot backend — REST layer, services, data access, caching, or async work. |
| `springboot-tdd` | Test-driven development for Spring Boot using JUnit 5, Mockito, MockMvc, Testcontainers, and JaCoCo. Use when adding features, fixing bugs, or refactoring. |
| `springboot-verification` | Verification loop for Spring Boot projects: build, static analysis, tests with coverage, security scans, and diff review before release or PR. |
| `team` | 多代理在共享任务清单上协同工作 |
| `test-real-skill` | 用于测试技能机制的示例技能 |
| `test-symlink-skill` | 验证 symlink 机制的示例测试技能 |
| `tinystruct-patterns` | Expert guidance for developing with the tinystruct Java framework. Use when working on the tinystruct codebase or any project built on tinystruct — including creating Application classes, @Action-mapped routes, unit tests, ActionRegistry, HTTP/CLI dual-mode handling, the built-in HTTP server, the event system, JSON with Builder/Builders, database persistence with AbstractData, POJO generation, Server-Sent Events (SSE), file uploads, and outbound HTTP networking. |
| `trace` | 以证据驱动并行追踪竞争假设并定位根因 |
| `translate` | Translate or update keys in packages/i18n/src/locales. Use whenever adding, changing, or reviewing strings across any target locale — enforces do-not-translate terminology, CLDR plural forms, placeholder/tag preservation, per-locale punctuation/register, and the AI-translation review workflow. Required reading before touching any *.json under src/locales. |
| `ui-to-vue` | Use when the user has UI screenshots or design exports that need batch conversion into Vue 3 components, especially with Vant, Element Plus, or Ant Design Vue. |
| `ultragoal` | 持久化多目标工作流并生成会话交接文本 |
| `ultraqa` | 测试、验证、修复循环直至达成目标 |
| `ultrawork` | 面向高吞吐任务并行的执行引擎 |
| `unified-memory` | Share durable, inspectable context and handoffs between Claude, Codex, Hermes, Cursor, OpenCode, and other agents through the local ECC Memory Vault. Use when an agent must save work state, transfer context, resume another agent's task, or search shared project knowledge. |
| `visual-verdict` | 截图对比的结构化视觉质量裁决 |
| `vite-patterns` | Vite build tool patterns including config, plugins, HMR, env variables, proxy setup, SSR, library mode, dependency pre-bundling, and build optimization. Activate when working with vite.config.ts, Vite plugins, or Vite-based projects. |
| `vue-patterns` | Vue.js 3 Composition API patterns, component architecture, reactivity best practices, Pinia state management, Vue Router navigation, and Nuxt SSR patterns. Activates for Vue, Nuxt, Vite, or Pinia projects. Use when building or reviewing Vue 3, Nuxt, or Pinia code — Composition API, reactivity, or router navigation. |
| `wiki` | 跨会话累积的持久化 Markdown 知识库 |
| `windows-desktop-e2e` | E2E testing for Windows native desktop apps (WPF, WinForms, Win32/MFC, Qt) using pywinauto and Windows UI Automation. Use when writing E2E tests for a Windows native desktop app with pywinauto or UI Automation. |
| `writer-memory` | 为作家追踪角色、关系、场景与主题的记忆系统 |

### languages
_各语言规范_

| 技能 | 用途 |
| --- | --- |
| `cpp-testing` | 配置并诊断 GoogleTest 与 CTest 及覆盖率 |

### misc
_其他_

| 技能 | 用途 |
| --- | --- |
| `configure-ecc` | 交互式安装 Everything Claude Code 技能与规则 |
| `continuous-learning-v2` | 基于本能观察会话并演化为技能的学习系统 |
| `nutrient-document-processing` | 用 Nutrient API 处理转换 OCR 各种文档 |
| `project-guidelines-example` | 基于真实应用的示例项目级技能模板 |
| `search-first` | 写自定义代码前先检索现有工具与库 |
| `security-scan` | 扫描 Claude Code 配置的安全漏洞与注入风险 |
| `skill-stocktake` | 审计 Claude 技能与命令的质量评估流程 |
| `strategic-compact` | 在合理节点手动压缩上下文以保留信息 |
| `verification-loop` | Claude Code 会话的全面验证系统 |

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
| `eval-harness` | 实现评估驱动开发的正式评估框架 |

### workflow
_开发流程_

| 技能 | 用途 |
| --- | --- |
| `blueprint-driven-development` | 按飞书产品蓝图逐小节实现标讯功能 |
| `brainstorming` | 创造性工作前探索用户意图、需求与设计 |
| `dispatching-parallel-agents` | 并行派发相互独立的任务给多个代理 |
| `executing-plans` | 在独立会话按检查点执行书面实现计划 |
| `finishing-a-development-branch` | 开发完成且测试通过后决定如何集成分支 |
| `google-code-review` | 执行 Google 风格的代码审查流程 |
| `html-first-workflow` | 以 HTML 优先的工作流开发前端 |
| `linear-task-creator` | 创建或更新 Linear 任务并套用项目模板 |
| `llm-knowledge-base` | 构建跨会话累积的 LLM 知识库 |
| `product-analysis` | 竞品分析、需求优先级与产品文档撰写 |
| `production-risk-review` | 对上线系统 PR 做生产风险审计 |
| `pseo` | 执行产品搜索优化相关的流程 |
| `receiving-code-review` | 收到审查反馈时严谨验证而非盲从 |
| `requesting-code-review` | 完成任务或合并前请求代码审查 |
| `speckit-chain` | 串联执行多个 Spec Kit 命令 |
| `standard-workflow` | 四阶段标准作业流程规划开发质检维护 |
| `subagent-driven-development` | 用子代理执行相互独立的实现计划 |
| `unified-dev-flow` | 当开始非简单的功能开发、修 bug、重构或迁移，需要决定走哪些阶段、调用哪些技能、走多深时使用。当用户问该用什么流程或技能时使用。触发词：统一流程 / 标准流程 / 开发流程 / 完整流程 / 走流程 / 端到端开发 / 该用什么技能 / 帮我选流程 / 怎么推进这个需求 / 规范流程。Use when deciding which dev workflow/skills to use for a non-trivial coding task. |
| `using-git-worktrees` | 用 git worktree 创建隔离的开发工作区 |
| `using-superpowers` | 开启会话时先调用技能再回应的流程 |
| `verification-before-completion` | 声明完成前先运行验证命令并确认结果 |
| `writing-plans` | 动代码前为多步任务编写实现计划 |
| `writing-skills` | 创建、编辑并在部署前验证技能 |
| `xiyu-code-review` | 按西域投标平台规范审查 PR 的架构与安全 |
| `xiyu-mode` | 西域投标管理平台专属模式（质疑复用优先+SpecKit流程+FP-Java+多Agent收尾） |
