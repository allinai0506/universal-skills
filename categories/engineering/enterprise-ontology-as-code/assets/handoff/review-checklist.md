# Ontology Review Checklist

- [ ] 业务对象不是简单按数据库表机械生成
- [ ] 所有 active 项有 Evidence
- [ ] ID 稳定且没有无意义重命名
- [ ] Relation 有明确业务问题
- [ ] 状态机没有隐藏跳转
- [ ] Rule 可独立判定
- [ ] 所有写操作通过 Action 暴露
- [ ] Action 有 precondition / auth / effect / idempotency / transaction / audit / failure
- [ ] Active Action 有真实 binding
- [ ] Policy 没有无意扩大权限
- [ ] Projection 遵循最小上下文原则
- [ ] Golden Case 已新增或更新
- [ ] Breaking Change 已明确
- [ ] Validator 通过
- [ ] 人工评审了 Action / Policy / Breaking Change
