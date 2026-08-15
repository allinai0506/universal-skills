# ai-release-engineer

用于 AI Coding 场景的代码验证、质量门禁、制品晋级、生产发布和回滚。

核心方法：

**Evidence → Gate → Release → Observe → Rollback**

## 使用方式

将此目录安装到 Agent 的 skills 目录。

触发场景：

- AI 完成代码修改后准备提交
- PR 合并前验证
- 准备部署测试/UAT/生产
- 生产发布前检查
- 生产异常后的回滚与复盘

## 设计原则

- 不以“代码看起来正确”作为完成标准
- 根据变更风险决定测试深度
- 核心业务流程使用真实 E2E 验证
- Build Once, Promote Same Artifact
- 生产必须可观察、可回滚
- 失败必须停止，不能靠降低测试标准获得 PASS

## 参考资料

- `references/quality-gate.md`：质量门禁
- `references/e2e-testing.md`：E2E 与关键业务路径
- `references/release.md`：制品与发布
- `references/rollback.md`：回滚
- `scripts/verify-release.sh`：本地基础检查模板
