# 10 Executable Knowledge

Ontology 不只描述“业务是什么”，还应让已验证的业务判断被 Agent、Workflow 和程序稳定复用。

Executable Knowledge 不是“把所有代码搬进 ontology/”。

## 原则

1. 生产 Domain Service 已是权威实现：Ontology 引用它，不复制逻辑。
2. 规则适合独立、确定性验证：可声明 check / binding。
3. 知识仍有争议：只能进入 proposal / experimental。

## 适合沉淀

- 完整性 / 就绪性检查
- 对账与一致性校验
- 状态转换 Guard
- 稳定业务计算
- 规范化 / 映射
- 已验证查询

## 必须明确

`id / business_meaning / inputs / outputs / authority / implementation_ref / failure_semantics / evidence / verification / lifecycle`

## 强制约束

- UNKNOWN 不得静默转换成 PASS、FALSE、“无异常”等正常业务结论。
- 不得为了“Ontology 可执行”复制已有权威业务逻辑。
- 可执行知识必须有测试或 Golden Case。
- Agent 可以执行已批准知识，但不能自行批准新知识。
