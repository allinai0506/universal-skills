# 04 Actions Runtime：从语义到真实执行

## Action 四层

### 1. Contract

业务允许做什么。

### 2. Guard

什么条件下允许做。

### 3. Binding

真实调用哪个实现。

### 4. Verification

执行后如何确认企业状态真的改变。

## 推荐 Action 文件字段

```yaml
id: archive_voucher
name: 归档凭证
lifecycle: active
target: accounting_voucher
inputs: []
preconditions:
  - voucher_source_complete
authorization:
  policies:
    - archivist_archive_policy
effects:
  state_transition:
    state_machine: voucher_lifecycle
    from: READY_TO_ARCHIVE
    to: ARCHIVED
side_effects:
  - create_archive_record
idempotency:
  strategy: business_key
  key: "voucher.id"
transaction:
  mode: atomic
  owner: archive-service
audit:
  required: true
failure_behavior:
  retry: safe_only
  compensation: none
bindings:
  - connector: archive_service
    operation: completeArchive
```

## 禁止事项

- Agent 直接拼 SQL 修改核心状态。
- Agent 绕过原系统 service 的校验。
- Action 没有幂等语义就允许自动重试。
- 只因为 HTTP 200 就认为 Action 成功。

## 执行后确认

至少一种：

- 重新读取目标 Object 状态。
- 接收权威事件。
- 校验事务结果。

Action 成功必须由业务状态确认，而不是由模型文本确认。
