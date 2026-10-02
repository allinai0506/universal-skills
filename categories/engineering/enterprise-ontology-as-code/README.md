# Enterprise Ontology-as-Code Skill v2.0

这是“语义对齐技能”的工程化升级版。

它不以术语表作为终点，而要求在目标仓库中建立可版本化、可验证、可评审、可运行的 `ontology/` 目录，并建立持续演化机制。

## 直接使用

把整个技能目录交给 Coding Agent，并给出：

```text
使用该技能对当前仓库执行 BROWNFIELD_DISCOVERY。
第一轮只读，不修改业务代码。
目标业务切片：<填写一个真实闭环>。
先生成 Evidence Inventory、Semantic Conflict Report 和 Candidate Ontology。
验证后再进入下一阶段。
```

新项目：

```text
使用该技能执行 GREENFIELD_BOOTSTRAP。
只围绕第一个真实业务闭环建立最小 Ontology，不做全企业建模。
目标闭环：<填写>。
```

已有 Ontology 的日常改动：

```text
使用该技能执行 EVOLUTION。
根据本次需求或缺陷生成 OEP，不直接修改 active 语义。
必须给出 Evidence、Ontology Diff、Golden Test 和 Breaking Change 判断。
```

## 目标仓库最终形态

见 `SKILL.md` 中的标准目录。

## 本包包含

- `SKILL.md`：Agent 的完整执行规范。
- `references/`：具体工程方法。
- `assets/templates/`：目标仓库 Ontology 模板。
- `assets/handoff/`：交付和评审模板。
- `scripts/`：验证、索引和差异检查脚本。
- `tests/`：脚本自测与合法/非法示例。
- `examples/`：电子会计档案、投标管理两个最小示例。
- `VALIDATION.md`：技能包自身验证方法。

## 设计来源

工程做法主要借鉴两类成熟实践：

- TextQL：Ontology-as-Code、Git 管理、从真实数据/文档逐步建设、Agent 提议修改、人审后合并、Golden Validation。
- Palantir：Object / Property / Link / Action，Data + Logic + Action + Security，Action 一等公民，运行时绑定、权限与审计。

本技能不是复刻任一产品，而是提取可在普通企业软件仓库中落地的最小工程规范。

## v2 推荐用法

对于已运行仓库，日常任务无需完整重建 Ontology。PR/CI 推荐执行：

```bash
python scripts/ontology_impact.py <base-ref> <head-ref> ontology
python scripts/ontology_validate.py ontology
```

详见 `references/10-executable-knowledge.md` 与 `references/11-ontology-impact-gate.md`。
