# 记忆系统

> 让 Agent 知道"上次分析到哪了"，避免每次从零开始。

---

## 为什么需要记忆

每次会话开始时，Agent 无法知道：
- "上次分析到 §4.2.1，结论是 3 项已实现、2 项未实现"
- "§4.2.3 缺 review_status 字段，这是在 6 月 4 日发现的"

记忆系统让历史结论可以被复用。

---

## 数据存储

- **主存储**：`${CLAUDE_PLUGIN_DATA}/gap-analysis-log.jsonl`（跨会话持久化）
- **备选**：`${WORKTREE}/.blueprint-data/gap-analysis-log.jsonl`
- **检查点**：`${WORKTREE}/.blueprint-checkpoint.json`

---

## 快速命令

```bash
SCRIPT=".claude/skills/blueprint-driven-development/scripts/memory-log.sh"

# 查看最近 3 条记录
bash "$SCRIPT" read --recent 3

# 查看特定小节
bash "$SCRIPT" read --section 4.2.1

# 对比两个小节
bash "$SCRIPT" diff 4.2.1 4.2.2

# 追加新记录（每次 Phase 2 完成后必须执行）
bash "$SCRIPT" append "4.2.1" "gap-analysis.md" "缺少budget/deadline字段"
```

---

## Session 开始时的流程

1. 运行 `memory-log.sh read --recent 3`
2. 告知用户上次分析状态
3. 如果目标小节与上次不同，询问是否覆盖

---

## JSONL 格式

每行一条记录（JSONL 格式，append-only）：

```json
{
  "timestamp": "2026-06-06T10:30:00Z",
  "section": "4.2.1",
  "worktree": "/path/to/worktree",
  "gap_file": "gap-analysis.md",
  "implemented": 3,
  "gaps": 2,
  "partial": 1,
  "notes": "缺少budget/deadline字段"
}
```
