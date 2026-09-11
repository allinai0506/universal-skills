# Unified Dev Flow 第二期：Task Execution Kernel 设计

**日期：** 2026-09-11

**状态：** 用户确认后修订

**依赖：** 第一期 Policy Router，分支基线 `85df28a`

**范围：** 纯 Python Task Execution Kernel、事件协议、Gate、Reducer、Evidence、Mock Provider、可信本地验证器与薄 CLI

## 1. 结论

第二期实现一个小而可证明的 **Task Execution Kernel**，不是通用工作流引擎。

第一期 Policy Router 仍然是路线、风险、保证级别、Controller 资格和交付授权的真相源。Router 把一次已经解析完成的决策固化为不可变 `RouteContract`；Kernel 只负责：

1. 接受带幂等键的命令；
2. 根据当前状态、`RouteContract` 和最新观察事实作出 Gate 决策；
3. 原子提交一批规范化领域事件；
4. 通过唯一 Reducer 重放状态；
5. 判断任务证据、复核声明和验收是否仍然新鲜；
6. 拒绝超过授权上限的交付操作。

运行状态写入目标项目的 `.unified-dev-flow/runs/<work-id>/`。现有 `.omc/`、`.superpowers/sdd/` 只作为未来只读兼容输入，不迁移、不改写。本期不初始化 `.codegraph/`。

## 2. 目标与非目标

### 2.1 目标

1. 定义严格、版本化的 `RouteContract`、`TaskContract`、Command、Event、Evidence Record 和 Review Assertion。
2. 建立单一状态权威：Gate 返回带 outcome 的领域事件批次，Reducer 是唯一状态转换解释器。
3. 用 append-only `events.jsonl` 支持恢复、审计、重放和命令级幂等。
4. 通过输入指纹和 revision binding，使旧 Evidence、Review Assertion 和 acceptance 可确定性失效。
5. 提供确定性 `MockProvider` 和明确标为可信执行的 `TrustedLocalVerifier`。
6. 提供 Python 库与薄 CLI，为后续 Codex、worktree、Herdr 等 Adapter 提供稳定边界。

### 2.2 非目标

- 不实现通用阶段引擎、工作流 DSL、waiver 系统或资源清理生命周期。
- 不启动或管理 AI Agent。
- 不创建 Codex task、Git worktree、Herdr Workspace/Tab/Pane/Clone。
- 不证明 Reviewer 的真实身份或独立性；本期只校验结构化 provenance 和新鲜度。
- 不提供 OS sandbox，不承诺阻止登记命令访问网络、Git 或项目外文件。
- 不实现常驻服务、Web API、UI、远程队列、多主写入或分布式锁。
- 不自动迁移、删除或重写 `.omc/`、`.superpowers/` 状态。
- 不实现 JSON 快照缓存；首期状态由小规模事件流直接重放。
- 不自动修复损坏的 JSONL 尾部。

## 3. 分层与权威边界

```text
Phase One Policy Router
    └── resolved immutable RouteContract
                    ↓
Command → Gate Decision → Event Batch → append-only Store
                                      ↓
                                  Reducer
                                      ↓
                               Derived Run State
                    ↑
        MockProvider / TrustedLocalVerifier
```

权威规则：

- Router 决定路线；Kernel 不重新解释 `workflow.json` 或重新选 Controller。
- Gate 决定命令能否产生事件，但不直接返回或写入新状态。
- Reducer 是唯一状态转换权威；任何状态变化都必须可由事件完整重放。
- Provider 只提供观察事实或验证结果，不追加事件、不接受任务、不完成 Run。
- CLI 只组装命令并调用库，不包含旁路状态逻辑。

建议代码结构：

```text
categories/workflow/unified-dev-flow/scripts/
├── unified-workflow
└── unified_workflow/
    ├── __init__.py
    ├── model.py
    ├── commands.py
    ├── events.py
    ├── reducer.py
    ├── gate_kernel.py
    ├── store.py
    ├── cli.py
    └── providers/
        ├── __init__.py
        ├── base.py
        ├── mock.py
        └── trusted_local.py
```

## 4. 项目运行目录与安全边界

```text
.unified-dev-flow/runs/<work-id>/
├── events.jsonl
├── evidence/
│   └── sha256-<digest>/
│       ├── stdout.bin
│       └── stderr.bin
└── run.lock
```

规则：

- `events.jsonl` 包含全部 Gate 语义所需数据，是可重放状态的唯一真相源。
- `evidence/` 是可选、不可变、内容寻址的诊断 blob；blob 缺失不改变事件语义，也不阻止 replay。
- 原始输出 blob 必须先完整写入、`fsync` 并原子发布，随后事件才可引用其 digest。崩溃可以留下未引用 blob；引用缺失或 digest 不符只产生诊断完整性警告，因为 Gate 所需数据已经内嵌事件。
- `run.lock` 只串行化 Kernel writer，不锁定项目编辑器，也不声称提供 workspace snapshot。
- `work-id`、`task-id`、`command-id`、`request-id` 仅允许 `[A-Za-z0-9][A-Za-z0-9._-]{0,127}`。
- 所有路径必须 `resolve` 后仍位于项目根或对应 run 目录内；控制目录及其父路径不得是符号链接。
- `.unified-dev-flow/**` 必须加入项目忽略规则，并从业务 workspace revision、scope diff 和 verification inputs 中排除。
- 控制目录和事件文件分别使用仅当前用户可访问的目录/文件权限；CLI 默认不输出完整命令环境或未截断的敏感输出。
- `delivery_target: patch` 是只读路线，不得创建 runtime；`init` 对该 RouteContract 返回 `RUNTIME_NOT_AUTHORIZED`。

## 5. 协议模型

所有顶层对象包含 `schema_version`。未知字段、未知枚举和未知 schema version 默认拒绝；升级通过显式迁移器处理。

### 5.1 RouteContract

`RouteContract` 是第一期 Router 的规范化输出，在 `RUN_CREATED` 中完整保存并计算 canonical JSON SHA-256：

```json
{
  "schema_version": 1,
  "resume": "fresh",
  "intent": "feature",
  "complexity": "medium",
  "risks": ["state_machine"],
  "domains": [],
  "delivery_target": "working_tree",
  "spec_backend": "unified",
  "controller": null,
  "proof_mode": "acceptance_test",
  "assurance_level": "adversarial",
  "review_limit": 3,
  "obligations": {
    "verification_claims": ["deterministic", "adversarial"],
    "accepted_review_provenance": ["cross_model", "human"],
    "required_delivery": "working_tree"
  },
  "source": {
    "policy_version": "2026.09.10-2",
    "policy_sha256": "sha256:..."
  }
}
```

本期不根据这些字段重新生成阶段列表。Router 必须把策略结论解析成有限且可机械校验的 `obligations`；Kernel 只检查这些固定义务，不从 `assurance_level` 猜测命令，也不重新解释一期策略。`review_limit` 和 `delivery_target` 仍是硬上限。

已启动 Run 不隐式跟随策略文件变化。未来如需改变 Contract，必须设计显式 `ROUTE_AMENDED` 事件及失效规则；该能力不在本期。

### 5.2 Run

Run 的派生字段：

```text
work_id
goal
route_contract / route_contract_sha256
status: active | blocked | completed | cancelled
review_rounds_by_task
blockers
latest_sequence / latest_hash
created_at / updated_at
```

`RUN_COMPLETED` 只表示 Kernel 管理的必需任务与已声明交付要求完成，不代表外部系统已经真实部署。

### 5.3 TaskContract

```json
{
  "schema_version": 1,
  "task_id": "task-001",
  "objective": "实现可验证的目标",
  "required": true,
  "dependencies": [],
  "write_scope": {
    "allowed_paths": ["src/**", "tests/**"],
    "forbidden_paths": [".env", ".git/**", ".unified-dev-flow/**"]
  },
  "verification_inputs": ["src/**", "tests/**", "pyproject.toml"],
  "acceptance": ["可观察的验收条件"],
  "verification_commands": [
    {
      "command_id": "unit",
      "argv": ["python3", "-m", "unittest"],
      "cwd": ".",
      "timeout_seconds": 60,
      "max_output_bytes": 1048576,
      "required": true,
      "claims": ["deterministic", "adversarial"]
    }
  ],
  "proof_mode": "acceptance_test",
  "required_review": "provenance_assertion"
}
```

路径使用项目根目录相对 POSIX glob。`forbidden_paths` 优先于 `allowed_paths`。可写 Task 的空 allowlist、绝对路径、父目录逃逸、控制目录写入和真实路径越界均非法。

`write_scope` 只控制允许的项目变化；`verification_inputs` 决定哪些变化会使 Evidence、Review Assertion 和 acceptance 失效。MVP 无法可靠判断依赖时，必须保守使用整个受管项目作为 `verification_inputs`，排除 `.git/**` 和 `.unified-dev-flow/**`。

### 5.4 Task 状态与派生满足条件

```text
draft → ready → running → waiting_review → accepted
                  ├──────────────→ ready       (report/verification failed)
                  ├──────────────→ blocked
                  └──────────────→ failed

waiting_review → ready       (NEEDS_FIXES)
waiting_review → blocked     (ESCALATE)
accepted       → stale       (inputs/contract/dependency invalidated)
stale          → ready       (dependencies currently satisfied)
blocked        → ready       (explicit blocker resolution)
```

`cancelled` 只允许通过显式 `TASK_CANCELLED` 进入；必需 Task 被取消后 Run 不能完成。本期没有 `cleaned` 状态。

任务的 `currently_satisfied` 是派生谓词，不是永久事实：

```text
state == accepted
AND accepted_task_revision == current_task_revision
AND accepted_input_fingerprint == current_input_fingerprint
AND accepted_verdict_fingerprint == current_fresh_verdict_fingerprint
AND every dependency currently_satisfied
```

依赖变化时，Reducer 依据显式 `TASK_INVALIDATED` 事件把受影响任务置为 `stale`。只有依赖重新 currently satisfied 后才能再次 `TASK_READIED`；`TASK_STARTED` 也必须重新检查依赖，不能依赖历史上的 ready 判定。Gate 在任何推进或完成命令前必须先比较当前 observation，并把所需失效事件放入同一事件批次。

### 5.5 WorkspaceRevision

核心协议使用 Provider 中立的 `WorkspaceRevision`：

```text
provider
revision_id
verification_input_fingerprint
changed_paths
observed_at
```

`TrustedLocalVerifier` 可额外记录 Git HEAD、tracked diff digest、untracked manifest 和相关文件内容 digest，但 Kernel 不把 Git 字段作为跨 Provider 必需字段。

`TASK_STARTED` 必须为当前 `task_revision` 持久化不可变的 `scope_origin`。后续 report 的 scope diff 是“当前 observation 相对 scope origin”的变化；验证命令的副作用则额外比较 pre-command 与 post-command revision。`NEEDS_FIXES` 和同一 revision 内的重试不得重采 origin，否则上一轮越界修改会被吸收为既有脏状态。只有显式 `TASK_INVALIDATED` 开启新 task revision 后才可建立新 origin；未解决的 `SCOPE_VIOLATION` 仍然阻止新 origin，必须先通过 blocker resolution 记录修复或人工处置 provenance。

MVP 在共享工作区一次只允许一个可写 Task 处于 `running`，避免把其他任务的合法变化错误归属给当前任务。首次启动该 revision 前已经存在的变化包含在 origin 中，之后的外部变化仍按当前任务期间变化处理并可能触发 scope violation。

### 5.6 Evidence Record

`VERIFICATION_RECORDED` 事件内嵌全部 Gate 相关数据：

- task revision、task contract hash、command id 与规范化 command hash；
- Provider 名称和版本；
- pre-command、post-command 和 commit-time `WorkspaceRevision`；
- 开始/结束时间、exit code、timeout/output-truncated 标记；
- stdout/stderr 长度、SHA-256 和可选 blob reference；
- scope diff 与 verification-input fingerprint；
- canonical evidence SHA-256。

仅 Agent 报告、时间戳、文件存在或 exit code 都不是充分 Evidence。

### 5.7 Review Assertion

`REVIEW_RECORDED` 记录：

- reviewer/provider 声明及 provenance 类型；
- 被审 Task Contract、源码输入、测试和 Evidence 指纹；
- `MERGE_READY | NEEDS_FIXES | ESCALATE`；
- 结构化 findings、时间和 canonical assertion SHA-256。

本期只证明“该 provenance 的复核声明已被记录且仍然新鲜”，不证明 Reviewer 身份或独立性。`MockReviewProvider` 只用于测试；真实身份认证和独立性证明留给未来 Adapter。

## 6. Command、事件批次与幂等

每个变更请求都是 Command：

```json
{
  "schema_version": 1,
  "request_id": "req-uuid",
  "command_type": "RECORD_VERIFICATION",
  "work_id": "work-123",
  "task_id": "task-001",
  "actor": {"type": "cli", "id": "local"},
  "expected_sequence": 11,
  "payload": {}
}
```

Store 先在锁内检查 `request_id`：

- 不存在：纯状态命令继续并在最终 batch 中直接 `REQUEST_RESOLVED`；有副作用命令先提交 `REQUEST_RESERVED`；
- 已存在已 resolution 且 fingerprint 相同：返回先前 outcome，不重复执行 Provider；
- 已存在 reservation、fingerprint 相同但无 resolution：返回 `REQUEST_IN_DOUBT`，不自动重跑；
- 已存在但 fingerprint 不同：返回 `IDEMPOTENCY_CONFLICT`。

MVP 使用同一个 Store 调用覆盖 reservation、Provider 执行和最终提交；该期间持有 run writer lock。进程在 reservation 后崩溃时，请求进入显式 `IN_DOUBT`，重试不会自动再次执行有副作用命令，需查询 Provider 或由人工解决。本期不宣称对外部进程副作用实现 exactly-once。

Gate 接口：

```python
Decision = decide(current_state, command, route_contract, observed_facts)

Decision = Decision(
    events: tuple[DomainEvent, ...],
    outcome: Allowed(result) | Denied(reason_code, required_actions),
)
```

`Decision.events` 是一个语义原子的事件批次。`Denied` 表示拒绝请求的目标推进，不表示禁止记录已经观察到的事实；因此一次被拒绝的完成请求仍可同批记录输入失效或 scope violation。例如第三次 `NEEDS_FIXES` 可以产生：

```text
REVIEW_RECORDED
TASK_INVALIDATED
TASK_BLOCKED
RUN_BLOCKED
ESCALATE_TO_HUMAN
```

Gate 不返回 `new_state`、`invalidated_evidence` 或只存在于内存中的 next actions。Reducer 顺序应用已提交事件；next actions 由状态纯函数派生。

每条 JSONL 记录是一个 `EventBatch` 信封，包含连续领域事件：

```json
{
  "schema_version": 1,
  "sequence": 12,
  "batch_id": "uuid",
  "request_id": "req-uuid",
  "request_sha256": "sha256:...",
  "work_id": "work-123",
  "occurred_at": "2026-09-11T00:00:00Z",
  "actor": {"type": "cli", "id": "local"},
  "previous_hash": "sha256:...",
  "events": [{"event_type": "TASK_INVALIDATED", "payload": {}}],
  "batch_hash": "sha256:..."
}
```

`batch_id` 只是事件身份；`request_id` 才是崩溃重试协议。`sequence` 连续，hash chain 覆盖完整 canonical batch。

首期领域事件：

```text
REQUEST_RESERVED     REQUEST_RESOLVED
RUN_CREATED          RUN_BLOCKED        RUN_RESUMED
RUN_COMPLETED        RUN_CANCELLED
TASK_ADDED           TASK_READIED       TASK_STARTED
TASK_REPORTED        VERIFICATION_RECORDED
TASK_WAITING_REVIEW  REVIEW_RECORDED    TASK_NEEDS_FIXES
TASK_ACCEPTED        TASK_INVALIDATED   TASK_BLOCKED
TASK_UNBLOCKED       TASK_FAILED        TASK_CANCELLED
SCOPE_VIOLATION      ESCALATE_TO_HUMAN  DELIVERY_RECORDED
```

`REQUEST_RESERVED` 持久化 request fingerprint、命令类型和 reservation sequence。`REQUEST_RESOLVED` 持久化稳定 outcome：`success | denied | provider_failure | abandoned`、reason code、返回摘要和关联事件。只有存在 reservation 且没有 resolution 的请求才是 `IN_DOUBT`。

本期不包含泛化 stage、waiver、cleanup 或资源分配事件。

## 7. Gate Kernel 规则

Gate Kernel 是纯函数，不读取文件、不运行命令、不追加日志。至少强制：

- `TASK_READIED`：Contract 完整、依赖 currently satisfied、路径策略合法。
- `TASK_STARTED`：再次确认依赖 currently satisfied；首次启动当前 task revision 时记录不可变 scope origin，重试时复用；存在未解决 scope violation 或其他可写 Task 正在运行时拒绝。
- `TASK_REPORTED`：报告字段满足命令 contract，commit-time revision 与报告 revision 相同。
- `VERIFICATION_RECORDED`：成功和失败结果都必须记录；只有成功、pre/post/commit observation 连贯、无 scope violation且与当前 task revision/inputs 相同的 Evidence 才能满足验证义务。失败结果使任务回到 `ready` 或 `stale`，但保留审计事实。
- `TASK_WAITING_REVIEW`：所有要求的 Evidence 当前新鲜，且新鲜验证命令 `claims` 的并集覆盖 RouteContract `obligations.verification_claims`。
- `TASK_ACCEPTED`：存在新鲜 `MERGE_READY` Review Assertion，且 provenance 类型属于 `obligations.accepted_review_provenance`；普通自述不能升级为独立证明。
- `TASK_NEEDS_FIXES`：任务回到 `ready`，当前 acceptance、Evidence 和 Review Assertion 失效；第三轮同时阻塞 Task/Run 并升级人工。
- 任何输入、Task Contract 或依赖变化：在推进事件之前生成 `TASK_INVALIDATED`，并级联重新打开受影响任务。
- scope diff 落在 `write_scope` 之外：记录 `SCOPE_VIOLATION` 并拒绝推进。
- `DELIVERY_RECORDED`：操作必须不高于 `patch < working_tree < commit < pr < merge < deploy` 的授权上限，并携带可验证 provenance、workspace revision 和 `acceptance_set_sha256`。该 hash 覆盖所有 required Task 当前有效的 acceptance/input/verdict 指纹。该事件记录声明，不执行交付操作。
- `RUN_COMPLETED`：所有 required Task currently satisfied、无 blocker，并且存在满足 `obligations.required_delivery`、绑定当前 `acceptance_set_sha256` 的交付声明。任务重新验收后，旧声明保留为历史但不再满足完成条件。

稳定 reason code 至少包括：

```text
INVALID_TRANSITION
INVALID_CONTRACT
DEPENDENCY_NOT_SATISFIED
SCOPE_VIOLATION
EVIDENCE_MISSING
EVIDENCE_STALE
VERDICT_MISSING
VERDICT_STALE
PROVENANCE_INSUFFICIENT
DELIVERY_NOT_AUTHORIZED
RUNTIME_NOT_AUTHORIZED
REVIEW_LIMIT_REACHED
IDEMPOTENCY_CONFLICT
REQUEST_IN_DOUBT
EXPECTED_SEQUENCE_MISMATCH
EVENT_SEQUENCE_BROKEN
EVENT_HASH_MISMATCH
LOCK_BUSY
```

## 8. Store、崩溃边界与恢复

普通纯状态命令：

1. 获取 `run.lock`；
2. 读取、解析、验证并 replay 完整事件流；
3. 检查 `request_id`、request fingerprint 和 `expected_sequence`；
4. 获取命令要求的最新 observation；
5. Gate 返回 `Decision(events, outcome)`；
6. 将领域事件与包含稳定 outcome 的 `REQUEST_RESOLVED` 组成完整 batch，编码为一行并追加、`flush`、`fsync`；
7. replay 新 batch，返回派生状态；
8. fsync 必要目录并释放锁。

验证命令额外执行：

1. 在调用 Provider 前以独立 batch 持久化 `REQUEST_RESERVED`；
2. 捕获 pre-command revision；
3. Provider 执行预登记命令并返回结果；
4. 捕获 post-command revision；
5. 发布可选 evidence blobs；
6. Store 在提交前再次观察 commit-time revision；
7. Gate 比较三个 revision，将验证事实、失效/违规事件和 `REQUEST_RESOLVED` 作为最终 batch 提交；即使目标推进被拒绝，也必须记录稳定 denied/provider_failure outcome。

这提供的是 **optimistic change detection**，不是隔离的 workspace snapshot。外部编辑器仍可能在最后观察后立刻修改文件；因此任何后续推进和验收都必须再次观察并使旧 acceptance 失效。

事件 JSON 损坏、序列断裂、hash 错误或未知 schema 时 fail closed。诊断 blob 缺失或 digest 不符产生 warning，但不改变 replay 状态。MVP 不自动截断尾行、不跳过坏记录；显式 repair/quarantine 工具延期。

无 `run.json`、`tasks.json`。`status` 在共享读锁或稳定 head 检查下 replay 小规模日志。未来只有测量证明需要时才引入单一 `state.json` 缓存，并必须带 `latest_sequence/latest_hash` 校验。

## 9. Provider

```python
class Provider(Protocol):
    name: str
    version: str

    def observe_workspace(self, request: ObserveRequest) -> WorkspaceRevision: ...
    def run_verification(self, request: VerificationRequest) -> VerificationResult: ...
```

### 9.1 MockProvider

- 从 fixture 返回确定性 observation、验证结果和异常；
- 覆盖成功、失败、超时、输出超限、revision drift 和 scope violation；
- 不访问真实网络或启动子进程。

### 9.2 TrustedLocalVerifier

- 只接受 TaskContract 中存在的 `command_id`；
- 使用 argv 数组和 `shell=False`，拒绝运行时命令字符串；
- cwd 必须解析在项目根目录内；
- 实施超时、输出上限和最小环境变量集合；
- 执行前后观察 workspace revision，并报告发生的路径变化；
- 不提供 Agent、commit、push、worktree 或 Herdr API。

它是一个拥有调用用户同等权限的**可信本地命令执行器**，不是 sandbox。登记命令仍可能访问网络、执行 Git 或写项目外路径；需要硬隔离时必须使用未来 OS sandbox Provider。

## 10. CLI

MVP 命令：

```text
unified-workflow init
unified-workflow task add
unified-workflow task ready
unified-workflow task start
unified-workflow task report
unified-workflow verify
unified-workflow review record
unified-workflow task accept
unified-workflow task resolve-blocker
unified-workflow delivery record
unified-workflow run complete
unified-workflow status
unified-workflow replay
unified-workflow request status
unified-workflow request resolve
```

每个变更命令要求 `--request-id`；支持 `--expected-sequence` 和 `--json`。`request status` 查询 reservation/outcome；`request resolve` 只允许将无法查询外部结果的 `IN_DOUBT` 请求显式标记为 `abandoned` 或记录人工核实的 outcome，并要求 actor/note provenance。它不会自动重跑命令。CLI 不接受任意命令字符串，不提供 generic/debug transition，不保留隐藏状态。

建议 exit code：

```text
0 success
2 invalid arguments or contract
3 gate denied
4 corrupt state
5 lock busy
6 provider/verification failure
7 request in doubt
```

`resume-probe`、`doctor` 和显式 tail repair 延至后续切片，避免兼容扫描与状态内核同时扩张。

## 11. 测试策略

全部测试使用 Python 标准库 `unittest`、`tempfile` 和受控子进程。

### 11.1 模型和路径安全

- 缺字段、未知字段、非法枚举、非法 ID、未知 schema 拒绝；
- RouteContract canonical hash 稳定且在运行期不可变；
- allowed/forbidden 冲突、真实路径逃逸、符号链接逃逸和控制目录写入拒绝；
- `patch` RouteContract 拒绝初始化 runtime。

### 11.2 Gate 与 Reducer

- 每个合法转换有成功用例，每个非法转换有拒绝用例；
- Gate 从不返回状态；Reducer 对同一事件流产生逐字段相同状态；
- 一个 NEEDS_FIXES 命令的失效、回退和第三轮升级属于同一 batch；Denied 请求也可同批持久化失效或违规事实；
- accepted 任务在 task/input/dependency/verdict 指纹变化后重新打开；
- required/optional/cancelled task 对 Run completion 的规则明确覆盖；
- Router obligations 的 verification claims、review provenance 和 required delivery 覆盖正反例；
- delivery ceiling 与 acceptance-bound delivery 覆盖全部有序目标和重新验收场景。

### 11.3 Store 与幂等

- 相同 request id + 相同 fingerprint 返回同一 outcome，Provider 只调用一次；
- 相同 request id + 不同 fingerprint 拒绝；
- reservation 后崩溃返回 `REQUEST_IN_DOUBT`，不盲目重跑；人工 resolution 可重放且保留 provenance；
- batch replay 保留失效和升级副作用；
- 两个 writer 竞争只有一个提交；
- JSON 尾行、序列和 hash 损坏 fail closed；诊断 blob 缺失或损坏只产生 warning。

### 11.4 Evidence 与并发观察

- pre/post/commit revision 漂移使 Evidence 或推进失效；
- `write_scope` 与 `verification_inputs` 分别测试；scope origin 能区分启动前脏状态与任务期间变化，NEEDS_FIXES 重试不能重置 origin 来隐藏越界修改；
- 第二个可写 Task 不能与第一个同时进入 running；stale Task 未满足依赖时不能 ready/start；
- `.unified-dev-flow/**` 变化不使业务 Evidence 自失效；
- blob 先发布后引用，未引用 orphan blob 不影响 replay；
- 后续源码变化使 Evidence、Review Assertion 和 acceptance 失效。

### 11.5 Provider 与 CLI

- MockProvider 覆盖全部确定性结果；
- TrustedLocalVerifier 仅执行登记 command id，拒绝 shell 字符串和 cwd 逃逸；
- 测试明确证明本地执行器不提供网络或文件系统 sandbox 保证；
- CLI JSON、reason code、exit code 和 request retry 结果稳定。

## 12. 端到端验收

必须在真实临时 Git 目录完成：

```text
init run with pinned RouteContract
→ add required dependent tasks
→ ready/start/report
→ verification fails
→ fix and record fresh verification
→ record fresh MERGE_READY provenance assertion
→ accept task
→ change a verification input
→ acceptance and dependents reopen
→ reverify and reaccept
→ record authorized delivery assertion bound to current acceptance set
→ complete run
→ replay events into byte-equivalent canonical state
```

同时证明：

1. 同一 request retry 不重复执行验证命令。
2. 禁止路径变化记录 `SCOPE_VIOLATION` 并阻止推进。
3. 交付声明不能高于 RouteContract 授权上限。
4. 重新验收后，旧 delivery assertion 不能完成 Run。
5. Reviewer provenance 不被描述为已认证的独立身份。
6. `.codegraph/` 缺失不影响运行，也不会被创建。
7. Runtime 不调用 Codex、Herdr、worktree 或任何 Agent。
8. `.omc/`、`.superpowers/sdd/` 保持零写入。

## 13. 实施切片

按可独立验证的依赖顺序实施：

1. strict models、canonical JSON、RouteContract/TaskContract 与路径安全；
2. EventBatch、request idempotency、Reducer 与无快照 replay；
3. Gate 转换矩阵、acceptance freshness、级联失效和 review limit；
4. Store 锁、request reservation、blob 发布和崩溃边界；
5. MockProvider 与 WorkspaceRevision 并发反例；
6. TrustedLocalVerifier 与验证 Evidence；
7. 薄 CLI 与完整端到端场景；
8. Router 文档接入、同步、验证和最终审查。

每一片先有失败测试，再实现。任何 verification input、Task Contract 或依赖变化都会使相交 Evidence、Review Assertion 和 acceptance 失效。

## 14. 被拒绝或延期的方案

### 14.1 通用 workflow.json 状态机

会复制第一期 Router 的策略权威，并迫使本期提前建模阶段、waiver、取消、清理和部署。改用不可变 `RouteContract` 输入。

### 14.2 Gate 返回 new_state

会与 Reducer 形成双重状态权威，Gate 的失效和升级副作用无法由日志重放。Gate 只返回拒绝或事件批次。

### 14.3 run.json + tasks.json 双快照

两个文件无法原子地表示同一代状态，而且小规模日志无需优化。MVP 直接 replay；未来只允许一个带 log head 校验的缓存。

### 14.4 LocalProvider 作为安全沙箱

`shell=False`、cwd 和环境白名单无法限制登记程序的网络、Git 或文件系统权限。明确降级为可信本地验证器，硬隔离交给未来 Adapter。

### 14.5 SQLite 首发

当前单机单写者无需数据库；JSONL 更便于审计和协议测试。若未来出现多写者或大日志，再以实际数据重新评估。

### 14.6 本期接入 Codex、Herdr 或 worktree

会同时引入协议与真实资源生命周期，无法隔离验证。先证明 Kernel，再实现 Adapter。

### 14.7 自动迁移或本期实现 resume-probe

旧 artifact 语义不统一，兼容扫描也与状态内核正交。本期保持只读、不迁移；后续单独设计 probe 输入输出和冲突分类。

### 14.8 自动修复 JSONL 尾部

未经审计的自动截断可能丢失已确认命令。MVP fail closed；后续增加显式 quarantine/repair 协议。

## 15. 后续接口预留

后续可以在不改变核心 `Command → Decision → EventBatch → Reducer` 语义的前提下增加：

- authenticated ReviewProvider；
- Codex AgentProvider；
- Git worktree/CoW CloneProvider；
- Herdr Workspace/Tab/Pane/Clone Provider；
- OS sandbox Provider；
- legacy resume-probe 与显式 repair 工具；
- 单一可丢弃状态缓存；
- 远程事件传输与观察 UI。

这些 Adapter 必须提交相同的 WorkspaceRevision、Evidence Record、Review Assertion 和 delivery provenance，不能成为新的流程真相源。
