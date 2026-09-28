# 技能包验证

## 1. 自身完整性

```bash
python scripts/ontology_validate.py tests/fixtures/valid/ontology
```

预期：退出码 0。

```bash
python scripts/ontology_validate.py tests/fixtures/invalid/ontology
```

预期：退出码非 0，至少报告引用不存在或 Action 契约缺失。

## 2. 单元测试

```bash
python -m unittest tests/test_validator.py
```

## 3. 目标仓库验收

至少检查：

- `ontology/ontology.yaml` 存在。
- active 项均有稳定 ID。
- 所有 relation 引用的 object 存在。
- 所有 action 的 target、rules、policies、bindings 可解析。
- 所有 action 声明 idempotency、transaction、audit、failure_behavior。
- 所有 projection 只引用存在的本体项。
- 至少一个 golden case。
- generated 文件没有被当作源文件编辑。
