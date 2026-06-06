# Phase 3 — 实现

---

## 前置条件

检查点 phase=3 且 `gap-analysis.md` 存在
门禁：`gap-analysis.md` 不存在 → **不能进入 Phase 3**

---

## 操作步骤

### 1. 按差距分析表逐个改动

优先处理"本次做"项。参考 `gap-analysis.md` 中的汇总表。

### 2. 编译验证（每改完一个大块都要做）

```bash
mvn compile -q          # 后端编译
npm run build           # 前端构建
```

> ⚠️ `mvn compile` 通过不代表 Spring 上下文能启动！改完要重启后端。

### 3. 权限变更

如果改了 `RoleProfileCatalog.java` 中的 `menuPermissions`：
- 必须写 Flyway 迁移脚本：`Vxxx__update_tender_role_permissions.sql`
- 迁移要对已有测试数据生效

### 4. E2E 测试（强制要求）

每个实现的功能点，至少写一个 Playwright 测试用例。参考 `references/playwright-verification.md`。

---

## 完成后

```bash
WORKTREE=$(git rev-parse --show-toplevel)
echo '{"section":"4.2.1","phase":4,"phases_done":[1,2,3],"worktree":"'"$WORKTREE"'"}' > "$WORKTREE/.blueprint-checkpoint.json"
```
