# 05 Security & Governance

## 最小模型

Policy 不要只写“管理员可操作”。

应该约束：

- subject：谁
- resource：什么对象/属性
- action：什么动作
- condition：什么条件
- scope：数据范围

## Agent 权限

默认：Agent 不拥有额外业务权限。

推荐模式：

1. `inherit_user`：继承发起人的权限。
2. `service_identity`：以受限服务身份运行。

禁止：

- Agent 看到用户无权访问的数据。
- Agent 因为“需要完成任务”而临时扩大权限。
- Tool 权限与 Ontology 权限脱节。

## 高风险变更

以下变化必须人工评审：

- 扩大 Action 可执行角色。
- 放宽数据读取范围。
- 新增跨系统写操作。
- 改变 Action effects。
- 改变状态机绕过路径。
