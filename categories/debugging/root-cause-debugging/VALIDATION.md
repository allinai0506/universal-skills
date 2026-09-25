# 打包验证记录

技能版本：1.0.0。说明文档核对日期：2026-09-25。

## 本次实际执行

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 校验器自动化测试 | 39 项通过 | validation/validator-tests.log |
| 合成旧实现的目标回归 | 失败，退出码 1，目标断言为 DRAFT != ARCHIVED | examples/atomic-archive/evidence/red.log |
| 合成修复实现的同一回归 | 通过，退出码 0 | examples/atomic-archive/evidence/green.log |
| 相邻正常行为 | 通过，退出码 0 | examples/atomic-archive/evidence/neighbor.log |
| 合成真实 SQLite 集成测试 | 3 项通过，退出码 0 | examples/atomic-archive/evidence/integration.log |
| 恢复原缺陷实现 | 同一目标断言再次失败，退出码 1 | examples/atomic-archive/evidence/reintroduced.log |
| 示例 diagnose / close 机械门禁 | 两阶段均通过 | 对 evidence.json 实际运行校验器 |
| 未填写模板 | 被拒绝，退出码 1 | validation/template-rejection.log |
| SKILL 元数据、相对链接、代码语法、JSON | 检查通过 | 打包过程静态检查 |

入口 SKILL.md 为 101 行。所有 Python 源文件通过 Python 3.9 语法级别解析；
实际执行环境为 Python 3.13.5，SQLite 版本和运行时间记录在演示 run-manifest.json。
“3.9+”是代码兼容目标，不代表已经在每个 Python 版本运行测试。

## 未验证范围

没有在用户的 Codex、Claude Code 或 OpenCode 实例中实际安装和触发。
没有读取、修改或运行真实业务仓库，没有连接生产数据库，也没有配置 CI 必需检查。
未进行真实缺陷样本对比试验，因此不声称已证明能降低项目 Bug 率。
机械校验成功不等于根因真实或业务验证充分；仍须审查真实执行、业务依据及修复范围。

## 校验器测试覆盖的重点

缺失或被改动的证据、重复标识、无效 JSON、未知引用、占位符、路径越界及符号链接越界；
修前修后场景/环境/版本不匹配、错误退出码、修后必需检查未通过、高风险缺少反证；
真实边界缺集成测试、日志证据不足、仅止血被误当修复，以及记录中的命令不被执行。

SHA256SUMS 提供包内各文件的 SHA-256（不含自身），用于核对解压内容，非作者身份签名。
