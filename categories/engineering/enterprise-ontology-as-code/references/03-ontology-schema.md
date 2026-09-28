# 03 Ontology Schema：最小可运行模型

## Object

不要把数据库表等同于业务对象。

对象应代表：

- 实体：客户、合同、凭证、档案
- 事件：付款、提交、审批、上传
- 关系实体：当关系自身有属性时，例如“凭证匹配关系”带匹配来源、置信度、确认人

## Relation

只建有业务语义的关系。

Direct Relation：关系没有自己的业务属性。

Object-backed Relation：关系有自己的状态/时间/角色/置信度等属性。

## State

状态机必须独立建模，不要藏在枚举里。

至少包含：

- initial
- terminal
- transitions
- guard_rules
- triggers

## Rule

Rule 必须可以独立执行或验证。

坏例子：

`archiveRule = 检查资料、审批、同步 ERP、生成档案号、发送消息`

好例子：

- `voucher_source_complete`
- `amount_consistent`
- `archive_period_closed`

## Action

Action 描述“允许改变什么”，不是描述 UI 按钮。

一个 Action 的 effects 应该是稳定业务语义，binding 可以替换。

例如：

`archive_voucher`

Effects：

- Voucher 状态变 ARCHIVED
- 创建 Archive 关系
- 写入 archived_at

Binding 可以从本地 service 换成远端 API，而不改变 Action ID。
