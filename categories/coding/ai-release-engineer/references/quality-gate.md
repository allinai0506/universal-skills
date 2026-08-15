# Quality Gate

## Gate 层级

### Gate 1 — Build

必须满足：

- 编译成功
- 依赖解析成功
- 必要构建产物生成

### Gate 2 — Automated Tests

按变更范围执行：

- Unit
- Integration
- API
- Regression

### Gate 3 — Static Quality

如果仓库已配置：

- SonarQube Quality Gate
- lint
- type check
- dependency/security scan

使用现有阈值，不要为了当前变更降低阈值。

### Gate 4 — Browser E2E

针对受影响的真实用户流程验证：

- 页面可进入
- 用户操作可完成
- API 调用正常
- 状态正确
- 数据结果正确

### Gate 5 — Business Critical Journey

对定义的核心业务链路做回归。

## 风险分级

```text
Low
→ Build + targeted tests

Medium
→ Build + Unit + Integration/API + targeted E2E

High
→ Full relevant regression + critical journeys + release review
```

不要机械地要求所有变更运行完整测试套件；重点是覆盖实际风险。

## PASS 原则

PASS 必须来自真实执行结果。

以下不能作为 PASS：

- “应该没问题”
- “代码看起来没问题”
- “之前测试过”
- “这个改动很小”
- “测试太慢所以跳过”
