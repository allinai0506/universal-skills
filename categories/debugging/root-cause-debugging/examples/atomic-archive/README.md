# 可执行示例：异常消失，不等于归档状态正确

这是合成场景，不是对当前电子会计档案项目的故障判断。
业务约定在 contract.md。测试通过真实 SQLite 连接验证状态，不 mock 持久化边界。
旧实现提前提交 ARCHIVED 状态，在回执写入前失败时留下部分提交。
修复把两次写入置于同一事务；同一注入点失败时回滚。

## 手动运行

在本目录使用已安装的 Python 3（标准库，无第三方依赖）：

```bash
ARCHIVE_IMPL=buggy python3 -m unittest -v test_archive
ARCHIVE_IMPL=fixed python3 -m unittest -v test_archive
ARCHIVE_IMPL=buggy python3 -m unittest -v test_archive
```

第一条和第三条命令预期返回非零退出码；目标失败为 test_interruption_rolls_back。
第二条预期三个测试全部通过。测试代码与断言未变，仅替换实现。
第三条恢复原缺陷实现，提供受控反例；这不是对任何真实仓库执行的 git revert 或线上故障注入。
脚本只在内存数据库创建合成数据，不连接客户数据库。

## 随包证据

`evidence/*.log` 是打包时真实执行的输出，`evidence.json` 引用这些输出及文件 SHA-256。
`evidence/run-manifest.json` 记录了实际 Python/SQLite 版本、运行时间、命令与退出码。
这些本地证据可复核，但并非签名的 CI 结果，不证明未测试的平台行为。

```bash
python3 ../../scripts/check_evidence.py evidence.json --phase diagnose
python3 ../../scripts/check_evidence.py evidence.json --phase close
```

教学日志能够帮助理解结构，不能用于关闭真实业务缺陷。
