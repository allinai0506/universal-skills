# Phase 5 — 验收与提交

---

## 前置条件

检查点 phase=5 且 Phase 4 验证通过

---

## 操作步骤

### 1. 运行测试套件

```bash
mvn test -q && npm test
```

### 2. 更新 `implementation-notes.md`

记录本节实现的功能点和遗留项。

### 3. 提交代码

```bash
WORKTREE=$(git rev-parse --show-toplevel)
cd "$WORKTREE"
git add gap-analysis.md implementation-notes.md verify-roles.md \
  backend/src/main/java/... src/views/...
git commit -m "feat(bid): §4.2.1 标讯创建功能实现

- 补齐 TenderListResponse 缺少的 budget/deadline 字段
- 新增审核状态流转：PENDING -> APPROVED/REJECTED
- 前端按钮权限与蓝图对齐
- gap-analysis: 3项已实现，2项未实现（本次不做）

refs: §4.2.1"
```

---

## 完成后

```bash
WORKTREE=$(git rev-parse --show-toplevel)
echo '{"section":"4.2.1","phase":0,"phases_done":[1,2,3,4,5],"worktree":"'"$WORKTREE"'"}' > "$WORKTREE/.blueprint-checkpoint.json"

# 更新记忆
bash .claude/skills/blueprint-driven-development/scripts/memory-log.sh \
  append "4.2.1" "gap-analysis.md" "完成"
```
