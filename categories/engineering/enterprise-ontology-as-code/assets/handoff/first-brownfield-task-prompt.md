# 第一个任务提示词：存量仓库 Ontology Discovery

你现在要使用 `Enterprise Ontology-as-Code & Continuous Evolution` 技能，对当前仓库执行 `BROWNFIELD_DISCOVERY`。

## 本轮目标

只完成 Ontology 的第一阶段发现与最小建模，不修改业务代码，不修改数据库，不改变运行行为。

## 范围

业务切片：`<替换成一个真实业务闭环>`

例如：

- 电子会计档案：`记账凭证 -> 原始凭证 -> 匹配 -> 完整性 -> 归档`
- 投标管理：`投标项目 -> 招标文件 -> 评分项解析 -> 评分结果持久化`

## 强制执行顺序

1. 阅读 `SKILL.md`。
2. Repository Archaeology：定位数据库、实体、枚举、状态转换、Service、API、权限、测试、UI 文案。
3. 建立 Evidence Inventory，区分 intended / implemented / observed。
4. 输出 Semantic Conflict Report，不自行解决冲突。
5. 建立最小 Candidate Ontology：Object -> Relation -> State -> Rule。
6. 暂时不要新增真实写 Action；可以列出候选 Action，但保持 experimental。
7. 复制/适配验证脚本并运行。
8. 输出最终 Handoff。

## 本轮禁止

- 不修改业务代码。
- 不修改 SQL migration。
- 不修 Bug。
- 不创建新的服务。
- 不把数据库表机械一一转换成 Object。
- 不把所有外键机械转换成 Relation。
- 不猜测业务真相。

## 必须交付

- `ontology/ontology.yaml`
- `ontology/objects/*`
- `ontology/relations/*`
- `ontology/states/*`
- `ontology/rules/*`
- `ontology/decisions/*` 或 `ontology/proposals/*`（存在冲突时）
- Evidence Inventory
- Semantic Conflict Report
- Validation Result
- Next Slice Recommendation

完成后不要继续进入第二阶段，等待人工审核。
