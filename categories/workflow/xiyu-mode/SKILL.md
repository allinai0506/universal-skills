---
name: xiyu-mode
description: 西域数智化投标管理平台专属工作模式。固化编码前置三问、日志与根因证据驱动、Spec Kit 流程门禁、FP-Java 架构约束、真实 API 零 Mock、多 Agent 隔离协作与自动化收尾纪律。在要求使用西域模式、/xiyu-mode 或按西域工程规范工作时调用。
disable-model-invocation: true
---

# 西域模式 (xiyu-mode)

西域数智化投标管理平台的专属工作规范与工程纪律。

## 1. 开场与交互纪律

第一句话必须主动打招呼：你好，同志！

开场声明当前环境：worktree 名称、当前分支、协作模式、是否主工作区。

结论先行。短句表达，一句话只说一个核心事实。

有独立判断。当用户需求不合理、存在冗余设计或增加用户心智负担时，直接指出问题并给出替代方案。拒绝盲目认同。

禁止废话套话。禁止使用“好的”、“没问题”、“马上为您办理”等机械回复。

禁用破折号连接符。禁用中句冒号。

## 2. 编码前置三问与根因定位

在修改或新增任何代码之前，必须严格执行三问：

1. **质疑。** 需求真正要解决的问题是什么？如果不做会有什么实际影响？能不能不做？
2. **复用。** 代码库中是否已经存在可以复用或修改的能力？优先级严格遵循 `复用 > 修改 > 组合 > 新建`。没有证明现有类、方法或组件不可用之前，严禁新建轮子。
3. **证据。** 修 Bug 严禁靠猜。必须按照 `docs/lessons/lessons-learned.md` 的全链路日志排查 SOP 查明根因。拿到日志与现场证据后再动手。

## 3. 架构与代码规范

后端严格遵循 FP-Java 规范。详见 `ARCHITECTURE.md`。

- 纯核心逻辑保持无副作用，可独立单测，不依赖 Spring 容器。
- Entity 与 DTO 严格分离。Controller 严禁直接返回 Entity。
- Controller 严禁直接依赖 Repository，必须通过 Service 或 Application 层调用。
- 单文件行数软上限 200 行，硬上限 300 行。

真实 API 唯一源，禁止 Mock。详见 `SECURITY.md`。

- 严禁在生产代码中引入 Mock 标志、Mock 适配器或假数据分支。

数据库迁移规范。详见 `ARCHITECTURE.md`。

- 表结构变更必须使用 `scripts/new-migration.sh` 或 `create-migration` 技能生成版本化迁移脚本与回滚脚本。
- 严禁修改已合入 main 的历史迁移文件。

前端规范。详见 `FRONTEND.md` 与 `DESIGN.md`。

- 样式必须使用 Design Token（CSS 变量）。严禁硬编码颜色与边距数值。
- 组件必须保持语义清晰与轻量，防范富文本等交互盲区。

## 4. 流程与质量门禁

复杂任务与新功能必须走 Spec Kit 流程门禁。详见 `PLANS.md`。

- 依次通过 `/speckit-specify`、`/speckit-plan`、`/speckit-clarify`、`/speckit-tasks`、`/speckit-implement` 推进，或直接运行 `/speckit-chain`。

每变必测。代码修改后必须执行对应测试套件与架构测试：

```bash
cd backend && mvn test -Dtest=ArchitectureTest -q
```

提交 PR 前必须执行代码审查与 QA 验证：

- 调用 `/xiyu-code-review` 审查架构边界与安全配置。
- 调用 `/qa` 或运行 E2E 测试验证交互链路。

## 5. 多 Agent 协作与收尾闭环

多 Agent 隔离纪律：

- 仅主工作区（`worktrees/trae`）允许启动后端、前端与 Sidecar 服务。其余 worktree 仅做代码编辑与 Git 操作。
- 严禁在 main 分支基准区直接修改代码。

每日早操 SOP：

```bash
git fetch origin && git rebase origin/main && bash scripts/sync-env.sh .
```

提交 PR：

- 通过 `scripts/gitee-pr-helper.sh` 或 Gitee API 创建 PR。
- 严禁使用 force-push 强推分支。

任务收尾标准流程：

1. 知识沉淀与 Wiki 回填。调用 `knowledge-capture` 技能，将 Bug 根因追加到 `docs/lessons/lessons-learned.md`，将新知识回填到 `.wiki/`。
2. 运行 `scripts/agent-finish-task.sh`，完成三重合入检查、清理文件锁并切回 main 基准分支。
