# 07 Continuous Evolution：让 Agent 提议，不能自我批准

## 触发条件

真实任务出现：

- 新术语
- 新别名
- 新业务关系
- 规则与代码冲突
- 状态含义变化
- Action 失败暴露隐式前置条件
- 多次重复的人工修正

## OEP 流程

```text
Observation
 -> Classify
 -> OEP
 -> Evidence
 -> Ontology Diff
 -> Golden Test
 -> Validate
 -> Human Review
 -> Merge
```

## OEP 必须回答

1. 发现了什么？
2. 证据是什么？
3. 当前 Ontology 哪里不够？
4. 提议修改什么？
5. 是否 Breaking？
6. 哪些 Agent/Workflow/App 会受影响？
7. 新增什么回归测试？

## 不应该沉淀为 Ontology 的内容

- 某一次客户临时要求。
- 单次运行中的瞬时事实。
- 纯技术实现细节。
- Agent 的猜测。

## v2：从 OEP 到可执行知识

当 OEP 涉及稳定、可重复的业务判断时，进一步判断是否属于 Executable Knowledge。若属于：指向现有权威实现或建立唯一实现；明确 UNKNOWN/failure semantics；增加 Golden Case/自动测试；明确 Agent/Workflow 消费者。Agent 可以提议，不能自我批准。
