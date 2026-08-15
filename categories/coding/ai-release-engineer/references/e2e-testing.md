# E2E Testing

## 目标

E2E 不追求覆盖所有页面，而是验证真实用户价值链。

优先建立少量 Critical User Journeys。

## 测试原则

```text
真实用户
→ 真实浏览器
→ 真实页面
→ 真实 API
→ 真实业务状态
→ 可验证结果
```

优先验证：

1. 登录与权限
2. 核心业务创建/处理
3. 状态流转
4. 数据持久化
5. 核心审批/提交
6. 最终业务结果

## AI QA Agent

AI 可以：

- 操作真实浏览器
- 按验收标准执行
- 读取页面状态
- 截图/记录失败现场
- 检查网络/API错误
- 分析日志
- 创建缺陷证据

AI 不可以：

- 因为找不到按钮就改变需求
- 自行修改业务验收标准
- 忽略失败继续宣布 PASS
- 为了通过测试修改测试预期

## Bug Evidence

每个失败至少记录：

```text
Scenario:
Expected:
Actual:
URL:
Step:
Error:
Screenshot:
Console / Network evidence:
Reproduction:
```

## 回归原则

修复 Bug 后：

```text
Bug
→ Regression Test
→ Fix
→ Re-run
```

修复不能只验证“现在不报错”，还必须验证原业务结果恢复。
