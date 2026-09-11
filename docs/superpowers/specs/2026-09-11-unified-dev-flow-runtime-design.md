# Unified Dev Flow 第二期：Core Runtime 与 Gate Kernel 设计

**日期：** 2026-09-11  
**状态：** 待用户书面复核  
**依赖：** 第一期 Policy Router，分支基线 `85df28a`  
**范围：** 纯 Python 协议、事件溯源状态机、Gate Kernel、Task Contract、Evidence、Mock/Local Provider 与薄 CLI

## 1. 结论

第二期把第一期的文档策略变成一个可重放、可审计、fail-closed 的本地核心运行时。它不替代 `unified-dev-flow` 的流程协议，也不承担业务实现；它只负责把候选事件与当前事实交给 Gate Kernel，判断状态能否推进，并将合法事件持久化。

本期采用 append-only event log 为唯一真相源，JSON 快照为可重建缓存。运行状态写入目标项目的 `.unified-dev-flow/runs/<work-id>/`。现有 `.omc/`、`.superpowers/sdd/` 只作为只读兼容输入，不自动迁移。

## 2. 目标与非目标

### 2.1 目标

1. 用版本化 Task Contract、Event、Evidence 和 Verdict 建立稳定协议。
2. 用纯函数 Gate Kernel 实施状态转换、依赖、范围、证据新鲜度、审查轮次和交付授权规则。
3. 以 append-only `events.jsonl` 支持恢复、审计、重放和幂等。
4. 用原子快照提供快速读取，并证明快照可以完全从事件重建。
5. 提供 MockProvider 和受限 LocalProvider，验证 Provider 边界而不启动 Agent。
6. 提供 Python 库与薄 CLI，供后续 Codex、worktree、Herdr 或其他执行后端复用。
7. 只读探测一期遗留状态，输出 Resume 分类与依据。

### 2.2 非目标

- 不启动或管理 AI Agent。
- 不创建 Codex task、Git worktree、Herdr Workspace/Tab/Pane/Clone。
- 不实现常驻服务、Web API、UI 或远程队列。
- 不自动迁移、删除或重写 `.omc/`、`.superpowers/` 状态。
- 不将 Agent 自述视为验证或验收证据。
- 不初始化 `.codegraph/`。
- 不实现多主写入、分布式锁或 SQLite 后端。

## 3. 分层架构

```text
unified-dev-flow policy protocol
              ↓
Python Core Runtime + Gate Kernel
              ↓
MockProvider / restricted LocalProvider
              ↓
future Codex / worktree / Herdr adapters
```

代码随技能安装：

```text
categories/workflow/unified-dev-flow/
├── workflow.json
└── scripts/
    ├── unified-workflow
    └── unified_workflow/
        ├── __init__.py
        ├── model.py
        ├── events.py
        ├── reducer.py
        ├── gate_kernel.py
        ├── store.py
        ├── cli.py
        └── providers/
            ├── __init__.py
            ├── base.py
            ├── mock.py
            └── local.py
```

职责边界：

- `model.py`：强校验值对象和序列化；拒绝未知字段。
- `events.py`：事件类型、schema version、序列号、幂等键和哈希链。
- `reducer.py`：从事件序列纯函数计算 Run/Task 快照。
- `gate_kernel.py`：校验候选事件，不执行命令、不写文件。
- `store.py`：锁、事件追加、fsync、快照原子替换和损坏检测。
- `providers/base.py`：事实观察与验证执行协议。
- `providers/mock.py`：确定性预设结果。
- `providers/local.py`：执行 Task Contract 中预登记的验证命令。
- `cli.py`：参数解析、调用库、稳定 JSON/文本输出与 exit code。
- `unified-workflow`：零逻辑入口脚本。

Coordinator 只读取状态、选择 Ready Tasks、请求外部调度并提交结果事件；它不写业务代码，也不绕过 Gate Kernel。

## 4. 项目运行目录

```text
.unified-dev-flow/runs/<work-id>/
├── events.jsonl
├── run.json
├── tasks.json
├── evidence/
│   └── <evidence-id>/
│       ├── record.json
│       ├── stdout.txt
│       └── stderr.txt
└── run.lock
```

规则：

- `events.jsonl` 是唯一真相源，只允许追加完整单行 JSON。
- `run.json`、`tasks.json` 是缓存；删除或损坏后可以 replay 重建。
- `evidence/` 保存命令结果和内容哈希；Event 只引用 evidence id 与摘要。
- `run.lock` 实施单写者。锁文件不承载流程状态。
- 不创建跨项目的全局 run registry；`work-id` 在目标项目内唯一。

## 5. 协议模型

所有顶层对象包含 `schema_version`。未知字段和未知枚举默认拒绝；兼容升级必须经过显式版本迁移器。

### 5.1 Run

关键字段：

```text
work_id
goal
policy_dimensions
controller
current_stage
delivery_target
status
review_round
waivers
next_actions
created_at / updated_at
```

Run 状态：

```text
draft → active → completed
           ├→ blocked
           └→ cancelled
blocked → active
```

### 5.2 Task Contract

```json
{
  "schema_version": 1,
  "task_id": "task-001",
  "objective": "实现可验证的目标",
  "dependencies": [],
  "allowed_paths": ["src/**", "tests/**"],
  "forbidden_paths": [".env", ".git/**"],
  "acceptance": ["可观察的验收条件"],
  "verification_commands": [
    {
      "command_id": "unit",
      "argv": ["python3", "-m", "unittest"],
      "cwd": ".",
      "timeout_seconds": 60,
      "max_output_bytes": 1048576
    }
  ],
  "proof_mode": "deterministic",
  "assurance_level": "deterministic",
  "agent_policy": {
    "may_edit": true,
    "may_commit": false,
    "may_network": false
  },
  "required_report_fields": ["changed_files", "verification", "concerns"]
}
```

路径使用项目根目录相对 POSIX glob。`forbidden_paths` 优先于 `allowed_paths`。绝对路径、父目录逃逸和空 allowlist 在可写 Task 中均非法。

### 5.3 Task 状态

```text
draft → ready → dispatched → running
                         ├→ waiting_review
                         ├→ blocked
                         └→ failed

waiting_review → needs_fixes → ready
waiting_review → verified → accepted
accepted → cleaned
```

`failed`、`cancelled` 和 `cleaned` 为终止态；重新执行通过新 Task 或显式补偿事件表达，不覆写历史。

### 5.4 Evidence

Evidence 至少记录：

- `evidence_id`、`task_id`、`command_id`；
- Provider 名称和版本；
- argv、cwd、开始/结束时间、exit code；
- stdout/stderr 路径、长度和 SHA-256；
- Git HEAD、相关 diff SHA-256；
- allowed scope 内相关文件的稳定清单与内容 SHA-256；
- 生成 Evidence 的事件 id。

任一依赖指纹变化会使相交 Evidence stale。仅 Agent 报告、仅时间戳、仅文件存在或仅 exit code 都不足以构成新鲜 Evidence。

### 5.5 Review Verdict

Verdict 包含 Reviewer 身份/Provider、被审 spec/diff/tests/evidence 指纹、结果 `MERGE_READY | NEEDS_FIXES | ESCALATE`、结构化 findings 和时间。源码、测试、Task Contract 或依赖 Evidence 改变后，旧 Verdict 失效。

## 6. Event Log

事件信封：

```json
{
  "schema_version": 1,
  "sequence": 12,
  "event_id": "uuid",
  "event_type": "TASK_VERIFIED",
  "work_id": "work-123",
  "task_id": "task-001",
  "occurred_at": "2026-09-11T00:00:00Z",
  "actor": {"type": "cli", "id": "local"},
  "causation_id": "uuid",
  "correlation_id": "uuid",
  "previous_hash": "sha256:...",
  "payload": {},
  "event_hash": "sha256:..."
}
```

首期事件至少包括：

```text
RUN_CREATED
RUN_ACTIVATED
RUN_BLOCKED
RUN_RESUMED
RUN_COMPLETED
RUN_CANCELLED
TASK_ADDED
TASK_READIED
TASK_DISPATCHED
TASK_STARTED
TASK_REPORTED
VERIFICATION_RECORDED
TASK_WAITING_REVIEW
REVIEW_RECORDED
TASK_NEEDS_FIXES
TASK_VERIFIED
TASK_ACCEPTED
TASK_BLOCKED
TASK_FAILED
TASK_CLEANED
EVIDENCE_INVALIDATED
SCOPE_VIOLATION
ESCALATE_TO_HUMAN
WAIVER_RECORDED
```

`event_id` 提供幂等性。完全相同的已存在事件视为成功重放；相同 id 但内容不同视为损坏。`sequence` 必须连续，`previous_hash` 与 `event_hash` 必须形成完整 SHA-256 链。

## 7. Gate Kernel

接口概念：

```python
Decision = gate(
    current_state,
    candidate_event,
    workflow_policy,
    observed_facts,
)
```

返回值只有：

```text
ALLOW(new_state, invalidated_evidence, next_actions)
DENY(reason_code, required_actions)
```

Gate Kernel 是纯函数，不读取文件、不运行命令、不追加事件。

关键规则：

- `TASK_READIED` 需要完整 Contract、依赖已 accepted、路径策略无冲突。
- `TASK_REPORTED` 需要全部 required report fields 和当前源码指纹。
- `TASK_VERIFIED` 需要所有必需命令 exit 0，Evidence 与当前事实一致。
- `TASK_ACCEPTED` 需要新鲜 `MERGE_READY` Verdict。
- `TASK_NEEDS_FIXES` 固定使任务回到 `ready`，并使相交 Evidence/Verdict 失效。
- 第三轮 `NEEDS_FIXES` 后产生 `ESCALATE_TO_HUMAN`，Run 进入 `blocked`。
- 允许路径之外或禁止路径之内的修改产生 `SCOPE_VIOLATION`，拒绝推进。
- `delivery_target` 为 `working_tree` 时，commit/push/PR/merge/deploy 事件均拒绝。
- `RUN_COMPLETED` 需要全部必需 Task accepted 或 cleaned、无未解决 blocker、无开放 waiver、必需阶段完成且未越权交付。

Reason code 是稳定 API，至少包括：

```text
INVALID_TRANSITION
INVALID_CONTRACT
DEPENDENCY_NOT_ACCEPTED
SCOPE_VIOLATION
EVIDENCE_MISSING
EVIDENCE_STALE
VERDICT_MISSING
VERDICT_STALE
DELIVERY_NOT_AUTHORIZED
REVIEW_LIMIT_REACHED
EVENT_SEQUENCE_BROKEN
EVENT_HASH_MISMATCH
LOCK_BUSY
```

## 8. Store、原子性与恢复

写入顺序：

1. 获取 `run.lock` 独占锁；
2. 读取、解析并验证完整事件流；
3. Gate Kernel 校验候选事件；
4. 追加事件，`flush` 并 `fsync`；
5. Reducer 计算新 Run/Task 快照；
6. 快照写入同目录临时文件；
7. `flush + fsync` 后使用原子 rename 替换目标；
8. fsync 父目录并释放锁。

事件已落盘而快照未更新时，下次命令自动 replay 并重建快照。快照损坏不阻塞恢复；事件 JSON 损坏、序列断裂、哈希错误或未知 schema version 必须 fail closed。首期不自动截断尾行、不跳过坏事件，也不猜测修复。

写操作、replay 和 verify 持独占锁。普通 status 可以读取完整原子快照；发现快照版本/序列落后时返回 stale 状态，要求 replay，不在无锁读路径隐式写入。

## 9. Provider

```python
class Provider(Protocol):
    name: str
    version: str

    def observe_workspace(self, request: ObserveRequest) -> WorkspaceFacts: ...
    def run_verification(self, request: VerificationRequest) -> Evidence: ...
```

Provider 只返回事实或 Evidence，不拥有状态机，不追加 Event，不把 Task 标记完成。

### 9.1 MockProvider

- 从测试 fixture 返回确定性 WorkspaceFacts 和 Evidence；
- 支持成功、失败、超时、输出超限和异常；
- 不访问真实网络或启动子进程。

### 9.2 LocalProvider

- 只接受 Task Contract 中存在的 `command_id`；
- 使用 argv 数组和 `shell=False`，拒绝运行时命令拼接；
- cwd 必须解析在项目根目录内；
- 实施超时、输出大小上限和环境白名单；
- 默认不提供网络、Agent、commit、push、worktree 或 Herdr 能力；
- 先观察事实，再运行命令，最后生成带指纹的 Evidence。

## 10. Resume 兼容

`resume-probe` 是只读操作。它检查 Git branch/worktree/HEAD/diff、`.omc/entry-gate-*`、`.superpowers/sdd/**/progress.md`、`.specify/` 与 `openspec/changes/`，输出：

```text
FRESH
MATCH
COMPATIBLE_DRIFT
CONFLICTING_DRIFT
```

结果包含命中的原生状态、比较依据、冲突和建议 next action。它不创建 run、不复制历史、不修改旧 artifact。由用户或上层 Controller 显式调用 `init`，并把 probe 报告作为 `RUN_CREATED` 的 provenance。

## 11. CLI

首期命令：

```text
unified-workflow init
unified-workflow task add
unified-workflow status
unified-workflow transition
unified-workflow verify
unified-workflow replay
unified-workflow resume-probe
unified-workflow doctor
```

所有命令支持 `--json`。CLI 不保留隐藏状态，不提供绕过 Gate Kernel 的 debug transition。错误输出包含稳定 reason code，并使用非零 exit code。`verify` 仅接受 task id 和 command id，不接受任意命令字符串。

建议 exit code：

```text
0 success
2 invalid arguments or contract
3 gate denied
4 corrupt state
5 lock busy
6 provider/verification failure
```

## 12. 数据流

```text
CLI/Controller request
→ Provider observes facts or records verification evidence
→ Core constructs candidate event
→ Gate Kernel returns ALLOW or DENY
→ Store appends allowed event under lock
→ Reducer rebuilds snapshots
→ CLI returns state and next_actions
```

所有推进均来自事件。Provider 输出、Agent 报告、命令 exit code 和 Reviewer Verdict 都只是候选事件的输入，必须经过 Gate Kernel。

## 13. 测试策略

全部测试使用 Python 标准库 `unittest`、`tempfile` 和受控子进程。

### 13.1 模型与 schema

- 缺字段、未知字段、非法枚举和非法路径拒绝；
- schema version 明确；
- 版本不兼容时 fail closed；
- allowed/forbidden 冲突和路径逃逸拒绝。

### 13.2 状态机与 Gate Kernel

- 每个合法转换至少一个成功用例；
- 每个非法转换至少一个拒绝用例；
- 依赖、scope、evidence、verdict、review limit 和 delivery gate 覆盖正反例；
- 重复 event id 幂等，内容冲突拒绝；
- 第三轮 NEEDS_FIXES 进入人工升级。

### 13.3 Store 与 replay

- 事件追加后、快照替换前崩溃可恢复；
- 快照缺失、过期或损坏可以重建；
- 事件断裂、哈希错误、尾行损坏拒绝继续；
- 两个 writer 竞争时只有一个成功；
- replay 与快照逐字段一致。

### 13.4 Provider 与 CLI

- MockProvider 覆盖成功、失败、超时、输出超限；
- LocalProvider 只执行登记命令，拒绝 shell 注入和 cwd 逃逸；
- CLI 文本/JSON、reason code 和 exit code 稳定；
- resume-probe 不产生写操作。

## 14. 端到端验收

必须完成以下真实临时目录场景：

```text
init run
→ add dependent tasks
→ dispatch and report
→ verification fails
→ needs_fixes
→ fresh verification passes
→ independent MERGE_READY verdict
→ accepted
→ run completed
→ delete snapshots
→ replay rebuilds byte-equivalent canonical state
```

同时证明：

1. 修改相关源码后旧 Evidence 失效。
2. 禁止路径变化产生 `SCOPE_VIOLATION`。
3. `working_tree` 不能记录 commit/push/PR/merge/deploy。
4. `.codegraph/` 缺失不影响运行。
5. Runtime 不调用 Codex、Herdr 或任何 Agent。
6. `resume-probe` 对 legacy 状态零写入。

## 15. 实施分解

二期实现计划应按以下依赖顺序切片：

1. workflow contract、严格模型与 schema 测试；
2. Event envelope、hash chain 与 reducer；
3. Gate Kernel 与完整转换矩阵；
4. Store、锁、原子快照与 replay；
5. MockProvider 与 LocalProvider；
6. CLI 与 resume-probe；
7. 端到端、崩溃恢复、并发和安全反例；
8. Router 文档接入、同步和最终审查。

每一片先有失败测试，再实现；任何源文件变化使相交验证与审查证据失效。

## 16. 被拒绝的方案

### 16.1 快照为真相源

实现较短，但日志与状态可能分叉，无法可靠 replay；后续异步 Adapter 会迫使重构。

### 16.2 SQLite 首发

事务能力强，但当前单机单写者不需要数据库；降低状态可读性、Git 友好性和零依赖可移植性。

### 16.3 本期直接接入 Codex 或 Herdr

会同时改变协议、状态机和真实执行资源，无法隔离验证。先用 Mock/Local 证明核心，再接执行 Adapter。

### 16.4 自动迁移 legacy 状态

旧 artifact 语义并不统一，自动迁移可能错误认领任务或证据。只读 probe 更安全。

## 17. 后续接口预留

后续阶段可在不改变 Gate Kernel 的前提下增加：

- Codex AgentProvider；
- Git worktree/CoW CloneProvider；
- Herdr Workspace/Tab/Pane/Clone Provider；
- 远程事件传输与观察 UI。

这些 Adapter 必须提交相同的 WorkspaceFacts、Evidence、Report 和 Verdict，不能成为新的流程真相源。
