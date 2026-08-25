# SKILLS-INDEX

> 技能来源速查表 · 自动生成于 2026-08-25 14:26 · 共 233 个一级技能。
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
| `gstack-autoplan` | 自动运行全套评审并给出决策的规划审查流程 |
| `gstack-benchmark` | 基准测试与页面性能回归检测 |
| `gstack-benchmark-models` | Cross-model benchmark for gstack skills. (gstack) |
| `gstack-browse` | 用无头浏览器做 QA 测试与网站自助验证 |
| `gstack-canary` | 部署后的金丝雀监控与错误告警 |
| `gstack-careful` | 为破坏性命令增设安全护栏与预警 |
| `gstack-codex` | OpenAI Codex CLI wrapper — three modes. (gstack) |
| `gstack-connect-chrome` | Launch GStack Browser — AI-controlled Chromium with the sidebar extension baked in. |
| `gstack-context-restore` | Restore working context saved earlier by /context-save. (gstack) |
| `gstack-context-save` | Save working context. (gstack) |
| `gstack-cso` | 执行 OWASP 与威胁建模的安全审计 |
| `gstack-design-consultation` | 咨询产品并产出完整设计体系与规范文档 |
| `gstack-design-html` | Design finalization: generates production-quality Pretext-native HTML/CSS. (gstack) |
| `gstack-design-review` | 设计师视角的视觉一致性审查与修复 |
| `gstack-design-shotgun` | Design shotgun: generate multiple AI design variants, open a comparison board, collect structured feedback, and iterate. (gstack) |
| `gstack-devex-review` | Live developer experience audit. (gstack) |
| `gstack-diagram` | Turn an English description (or mermaid source) into a diagram triplet: the source, an editable .excalidraw file you can open (gstack) |
| `gstack-document-generate` | Generate missing documentation from scratch for a feature, module, or entire project. (gstack) |
| `gstack-document-release` | 发布上线后更新项目文档与版本号 |
| `gstack-freeze` | 冻结当前工作状态以便安全切换上下文 |
| `gstack-gstack-upgrade` | Upgrade gstack to the latest version. |
| `gstack-guard` | 为工作流设置质量门禁与守护 |
| `gstack-health` | Code quality dashboard. (gstack) |
| `gstack-investigate` | 调查并定位问题或回归的根源 |
| `gstack-ios-clean` | Remove the DebugBridge SPM package and all #if DEBUG wiring from an iOS app. (gstack) |
| `gstack-ios-design-review` | Visual design audit for iOS apps on real hardware. (gstack) |
| `gstack-ios-fix` | Autonomous iOS bug fixer. (gstack) |
| `gstack-ios-qa` | Live-device iOS QA for SwiftUI apps. (gstack) |
| `gstack-ios-sync` | Regenerate the iOS debug bridge against the latest upstream gstack templates. (gstack) |
| `gstack-land-and-deploy` | 合并分支并部署上线的一体化流程 |
| `gstack-landing-report` | Read-only queue dashboard for workspace-aware ship. (gstack) |
| `gstack-learn` | Manage project learnings. |
| `gstack-make-pdf` | Turn any markdown file into a publication-quality PDF. (gstack) |
| `gstack-office-hours` | 定时答疑与协作支持的在线时段流程 |
| `gstack-open-gstack-browser` | Launch GStack Browser — AI-controlled Chromium with the sidebar extension baked in. |
| `gstack-pair-agent` | Pair a remote AI agent with your browser. (gstack) |
| `gstack-plan-ceo-review` | 以产品视角评审规划方案的合理性 |
| `gstack-plan-design-review` | 在实现前评审设计的规范与质量 |
| `gstack-plan-devex-review` | Interactive developer experience plan review. (gstack) |
| `gstack-plan-eng-review` | 以工程视角审查规划的技术可行性 |
| `gstack-plan-tune` | Self-tuning question sensitivity + developer psychographic for gstack (v1: observational). (gstack) |
| `gstack-qa` | 执行质量保证测试与缺陷验证流程 |
| `gstack-qa-only` | 仅执行质量测试而不修改代码 |
| `gstack-retro` | 召开回顾会议复盘并提炼改进项 |
| `gstack-review` | 多角度代码与方案的综合评审 |
| `gstack-scrape` | Pull data from a web page. (gstack) |
| `gstack-setup-browser-cookies` | 配置浏览器登录态与 Cookie 以便自动化 |
| `gstack-setup-deploy` | 配置部署环境与发布流程 |
| `gstack-setup-gbrain` | Set up gbrain for this coding agent: install the CLI, initialize a local PGLite or Supabase brain, register MCP, capture per-remote trust policy. (gstack) |
| `gstack-ship` | 完成发布上线并处理版本流程 |
| `gstack-skillify` | Codify the most recent successful /scrape flow into a permanent browser-skill on disk. (gstack) |
| `gstack-spec` | Turn vague intent into a precise, executable spec in five phases. (gstack) |
| `gstack-sync-gbrain` | Keep gbrain current with this repo's code and refresh agent search guidance in CLAUDE.md. Wraps the gstack-gbrain-sync orchestrator with state (gstack) |
| `gstack-unfreeze` | 解除冻结状态以恢复工作 |

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
| `autopilot` | 从想法到可运行代码的全自主执行 |
| `autoresearch` | 带严格评估合约的单任务持续改进循环 |
| `blueprint-e2e` | 为飞书产品蓝图每小节独立编写并执行 E2E 测试 |
| `configure-notifications` | 用自然语言配置 Telegram、Discord 与 Slack 通知 |
| `create-migration` | 生成 Flyway 迁移脚本并做格式校验 |
| `deep-dive` | 两阶段管线做因果追踪与需求澄清的深度调查 |
| `deep-interview` | 苏格拉底式深度访谈并澄清需求中的数学歧义 |
| `deepinit` | 用分层 AGENTS.md 文档深度初始化代码库 |
| `external-context` | 并行调用文档专家代理做外部检索与查询 |
| `github-sync` | 在 GitHub 与 Gitee 之间双向同步西域项目代码 |
| `gstack` | Router for the gstack skill suite. (gstack) |
| `hud` | 配置 HUD 显示布局、预设与元素 |
| `impeccable` | 全面设计、审查并打磨各种前端界面 |
| `knowledge-capture` | 捕获并沉淀开发过程中的知识与经验 |
| `learner` | 从当前对话中提炼可复用的技能 |
| `mcp-setup` | 配置常用 MCP 服务器以增强代理能力 |
| `parse-prd` | 解析飞书 PRD 文档为结构化需求简报 |
| `project-session-manager` | 以工作树优先管理开发环境与工单会话 |
| `ralph` | 带可配置验证评审的自循环任务执行 |
| `ralplan` | 执行前对模糊请求做共识规划的入口 |
| `release` | 分析仓库发布规则并引导完成发布流程 |
| `self-improve` | 用锦标赛选择实现代码的自主进化改进 |
| `setup` | 把安装诊断与 MCP 请求路由到正确流程 |
| `skill` | 列出、添加、移除并搜索本地技能 |
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
| `team` | 多代理在共享任务清单上协同工作 |
| `test-real-skill` | 用于测试技能机制的示例技能 |
| `test-symlink-skill` | 验证 symlink 机制的示例测试技能 |
| `trace` | 以证据驱动并行追踪竞争假设并定位根因 |
| `ultragoal` | 持久化多目标工作流并生成会话交接文本 |
| `ultraqa` | 测试、验证、修复循环直至达成目标 |
| `ultrawork` | 面向高吞吐任务并行的执行引擎 |
| `visual-verdict` | 截图对比的结构化视觉质量裁决 |
| `wiki` | 跨会话累积的持久化 Markdown 知识库 |
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
| `entropy-reduction` | 设计边界清晰且低复杂度的模块化代码 |

### security-review
_安全审查_

| 技能 | 用途 |
| --- | --- |
| `security-review` | 安全审查清单与策略 |

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
| `unified-dev-flow` | 当开始非简单的功能开发、修 bug、重构或迁移，需要决定走哪些阶段、调用哪些技能、走多深时使用。当用户问该用什么流程或技能时使用。触发词：统一流程 / 标准流程 / 开发流程 / 完整流程 / 走流程 / 端到端开发 / 该用什么技能 / 帮我选流程 / 怎么推进这个需求 / 规范流程。 |
| `using-git-worktrees` | 用 git worktree 创建隔离的开发工作区 |
| `using-superpowers` | 开启会话时先调用技能再回应的流程 |
| `verification-before-completion` | 声明完成前先运行验证命令并确认结果 |
| `writing-plans` | 动代码前为多步任务编写实现计划 |
| `writing-skills` | 创建、编辑并在部署前验证技能 |
| `xiyu-code-review` | 按西域投标平台规范审查 PR 的架构与安全 |
| `xiyu-mode` | 西域投标管理平台专属模式（质疑复用优先+SpecKit流程+FP-Java+多Agent收尾） |
