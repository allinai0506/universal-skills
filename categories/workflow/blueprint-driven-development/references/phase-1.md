# Phase 1 — 蓝图分析

> 读取飞书蓝图文档，提取目标小节的功能点、权限矩阵、状态流转。

---

## 前置条件

检查点 phase=1
门禁：如果 phase > 1，跳到对应 Phase 继续

---

## 操作步骤

### 1. 查询记忆（Session 开始时）

```bash
bash .claude/skills/blueprint-driven-development/scripts/memory-log.sh read --recent 3
```

如果上次分析的 section 与目标不一致，告知用户。

### 2. 读取蓝图文档目录

```bash
lark-cli docs +fetch --api-version v2 \
  --doc "<BLUEPRINT_URL>" \
  --scope outline --max-depth 5
```

### 3. 找到目标小节的 block-id

从目录中定位目标小节（如 4.2.1），记录其 `block_id`。

### 4. 读取目标小节正文

```bash
lark-cli docs +fetch --api-version v2 \
  --doc "<BLUEPRINT_URL>" \
  --scope section \
  --start-block-id "<BLOCK_ID>" \
  --detail full --format pretty
```

### 5. 提取关键信息

输出到 `implementation-notes.md`，记录：

- 功能点列表（含字段名、类型、约束）
- 权限矩阵（哪个角色能做什么）
- 状态流转图
- API 接口定义（URL、请求/响应字段）
- 蓝图原文中所有可验证的细节

### 6. 更新检查点

```bash
WORKTREE=$(git rev-parse --show-toplevel)
echo '{"section":"4.2.1","phase":2,"phases_done":[1],"worktree":"'"$WORKTREE"'"}' > "$WORKTREE/.blueprint-checkpoint.json"
```
