# 02 Brownfield Discovery：存量仓库反向恢复

## 第一轮只读

Agent 第一次进入成熟仓库时禁止“顺手修代码”。

先产出证据。

## 建议搜索顺序

1. 数据库 migration / schema
2. domain/entity/model
3. enum / status / type
4. service 中的状态转换
5. controller/API contract
6. message/event
7. permission/role/authorization
8. tests
9. UI labels/form
10. docs/readme

## Evidence Record

每个候选语义都记录：

```yaml
claim: "ARCHIVED 表示已完成法定归档"
kind: implemented
source: src/main/java/.../ArchiveService.java
locator: "completeArchive"
confidence: high
notes: "函数成功后写 archived_at"
```

kind 只能是：

- intended
- implemented
- observed

## 冲突处理

例：

- 文档：MATCHED 表示“全部原始凭证已匹配”
- 代码：只要匹配一张就设置 MATCHED
- 生产数据：MATCHED 记录仍有缺失附件

输出：

```text
Semantic Conflict SC-001
Term: MATCHED
Intended: 全量匹配完成
Implemented: 至少一条匹配关系
Observed: 存在缺失附件
Decision: unresolved
```

不要替业务方拍脑袋决定。

## Candidate -> Active

候选本体必须经过：

Evidence -> Review -> Test -> Merge

未经确认的项 lifecycle 保持 experimental。
