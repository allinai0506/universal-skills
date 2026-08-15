# Rollback

## 原则

生产异常时：

**Rollback first, investigate second.**

不要把 Production 当成调试环境。

## 回滚前确认

- 当前生产 Artifact
- 上一个稳定 Artifact
- 数据库迁移状态
- 配置变更
- Feature Flag 状态
- 关键错误指标

## 常见回滚方式

### Application Rollback

将生产切回上一个已验证 Artifact。

### Feature Flag

如果功能由 Feature Flag 控制：

```text
Flag ON
→ Problem
→ Flag OFF
```

这是优先级很高的低风险回滚手段。

### Database

数据库变更必须优先设计向后兼容。

推荐：

```text
Expand
→ Deploy
→ Migrate
→ Contract
```

避免应用回滚后数据库结构已经无法兼容。

## 回滚后

1. 验证核心业务流程
2. 验证错误率恢复
3. 保存日志与指标
4. 创建缺陷
5. 增加回归测试
6. 修复
7. 重新走 Quality Gate
8. 创建新 Artifact

## 禁止

- 直接修改生产代码
- 临时删除数据
- 修改测试结果
- 用未验证代码覆盖稳定版本
