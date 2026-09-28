# 08 Test Strategy

## 1. Schema Tests

文件字段是否满足最低契约。

## 2. Reference Integrity

- relation.from/to object 必须存在。
- action.target 必须存在。
- action.preconditions rule 必须存在。
- action.policy 必须存在。
- binding.connector 必须存在。

## 3. State Tests

- initial 状态存在。
- terminal 状态存在。
- transition from/to 合法。
- 不存在未声明跳转。

## 4. Golden Cases

Golden Case 不是只测 parser，而是测业务定义。

例：

```yaml
case: 完整凭证允许归档
facts:
  source_documents: 3
  required_documents: 3
  period_closed: true
expected:
  rules:
    voucher_source_complete: true
  allowed_actions:
    - archive_voucher
```

## 5. Breaking-change Tests

以下变化自动标红：

- active ID 删除/重命名
- required property 删除
- relation cardinality 改变
- action effect 改变
- policy scope 扩大
- state transition 删除

## 6. Production Feedback

高频 Action 失败要反向检查：

- 是否漏了 precondition？
- mapping 是否错误？
- policy 是否错误？
- 状态机是否与现实不符？

不是先调 Prompt。
