# 11 Ontology Impact Gate

## 目标

不要求每个 PR 都修改 Ontology；要求每个可能影响业务语义的 PR 显式回答：**这次修改有没有 Ontology Impact？**

结果：`changed / none / unknown`。

- changed：业务语义变化，应同步 Ontology。
- none：触达敏感区域但没有语义变化，必须给 reason + evidence。
- unknown：证据不足，必须人工 Review。

## 为什么需要 Gate

AGENTS.md 是行为约束，Agent 可能遗漏。Gate 检查最终 Git Diff，是独立的第二道防线。

`ontology_impact.py` 是确定性启发式门禁，不假装理解全部业务语义。它结合路径、文件类型、Diff 敏感词、Ontology Diff 和 `.ontology-impact.yaml` 判断是否需要 Review。

## 推荐规则

1. 未命中风险：PASS。
2. 命中风险且 Ontology 同步变化：PASS，并继续 ontology_validate。
3. 命中风险、Ontology 未变化，但有有效 `impact: none`：PASS_WITH_DECLARATION。
4. 命中风险且无声明：REVIEW_REQUIRED。
5. impact=unknown：REVIEW_REQUIRED。
