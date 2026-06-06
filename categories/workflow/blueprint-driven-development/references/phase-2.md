# Phase 2 — 差距分析

> **最关键的阶段。Phase 2 失败是实现偏差的根因。**
>
> **开始前必读：`references/gotchas.md`**

---

## 目标

回答核心问题：**"蓝图上这一段的功能，在当前代码库里有没有完整实现？"**

完整实现 = 四个维度全部对齐：

| 维度 | 验证内容 |
|------|---------|
| **后端 API** | 接口存在、请求/响应字段对齐、权限控制正确 |
| **前端 UI** | 页面/组件存在、表单字段与蓝图对齐、按钮权限正确 |
| **数据库** | 表字段存在、数据类型正确、索引完整 |
| **业务流程** | 状态流转符合蓝图定义 |

---

## 禁止的行为

- 只 grep 文件是否存在就写"已实现"
- 只看前端有组件不看后端有 API
- 只看字段名存在不看字段类型和校验规则
- 把"有类似功能"当"已完整实现"
- 引用 commit message 作为证据（见 gotchas.md G6）

---

## 步骤 1：提取蓝图要求清单

从 Phase 1 的蓝图正文中提取所有可验证的功能点：

```markdown
| # | 功能点描述 | 类型 | 优先级 | 蓝图原文 |
|---|---------|------|--------|---------|
| 1 | 标讯列表查询接口 | 后端 API | P0 | GET /api/tenders... |
```

---

## 步骤 2：逐项验证（每个功能点必须完成全部 4 个维度）

### 后端 API 验证

```bash
# 1. 找 Controller
grep -rn "class.*Controller" backend/src/main/java/com/xiyu/bid/tender/ --include="*.java" | grep -i "tender\|标讯"

# 2. 找接口定义（URL + HTTP 方法）
grep -rn "@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping" \
  backend/src/main/java/com/xiyu/bid/tender/ --include="*.java" | head -30

# 3. 验证 DTO 字段（⚠️ 必须检查完整声明，不是只 grep 字段名）
grep -rn "class.*Request\|record.*Request\|class.*Response\|record.*Response" \
  backend/src/main/java/com/xiyu/bid/tender/dto/ --include="*.java" | head -20

# 4. 验证字段类型（用 -B 1 -A 1 看上下文）
grep -rn "private.*budget\|private.*status\|private.*deadline" \
  backend/src/main/java/com/xiyu/bid/tender/ --include="*.java" -B 1 -A 1

# 5. 验证枚举值（⚠️ 必须逐个核对数量）
grep -rn "enum.*Status" backend/src/main/java/com/xiyu/bid/tender/ --include="*.java" -A 30
```

### 前端 UI 验证

```bash
# 1. 找页面组件
find src/views -name "*.vue" | xargs grep -l "tender\|标讯" | head -10

# 2. 验证字段绑定（字段名 + 类型）
grep -rn "budget\|status\|deadline\|审核" \
  src/views/Bidding/ --include="*.vue" | head -30

# 3. 验证权限指令
grep -rn "v-if\|v-permission\|v-show" \
  src/views/Bidding/ -A 1 --include="*.vue" | grep -i "tender\|审核" | head -20

# 4. 验证 API 调用
grep -rn "getTenderList\|createTender\|submitTender\|approveTender" \
  src/api/ --include="*.js" | head -20
```

### 数据库验证

```bash
# 1. 找对应表
grep -rn "CREATE TABLE.*tender\|CREATE TABLE.*bid" \
  backend/src/main/resources/db/migration-mysql/V*.sql | tail -10

# 2. 验证关键字段（字段名）
grep -rn "budget\|status\|deadline\|review_status\|reviewed_by" \
  backend/src/main/resources/db/migration-mysql/V*.sql | tail -20

# 3. 验证字段类型和约束
grep -rn "VARCHAR\|INT\|BIGINT\|DECIMAL\|ENUM" \
  backend/src/main/resources/db/migration-mysql/V*.sql | grep -i tender | head -20

# 4. 验证菜单权限 INSERT（⚠️ Gotcha G4）
grep -rn "INSERT.*menu_permission\|menu_permission.*INSERT" \
  backend/src/main/resources/db/migration-mysql/V*.sql | grep -i tender
```

### 业务流程验证

```bash
# 1. 找状态枚举
grep -rn "enum.*Status\|enum.*State\|Status.*enum" \
  backend/src/main/java/com/xiyu/bid/tender/ --include="*.java" | head -10

# 2. 验证状态流转逻辑
grep -rn "PENDING\|APPROVED\|REJECTED\|状态" \
  backend/src/main/java/com/xiyu/bid/tender/service/ --include="*.java" | head -20
```

---

## 步骤 3：写出差距分析表

使用 `references/gap-analysis-examples.md` 中的模板，格式为 `gap-analysis.md`：

每个结论必须附带"验证命令 + 实际输出"。无法用命令验证的结论不得写入。

---

## 步骤 4：交叉验证（防止误判 — 必须做）

在写入 gap-analysis.md 之前，对每个结论做反向验证：

```bash
# 对每个"已实现"的结论 → 确认代码确实存在
grep -rn "budget" backend/src/main/java/com/xiyu/bid/tender/dto/TenderListResponse.java

# 对每个"未实现"的结论 → 确认不存在
grep -rn "duplicate\|dedup\|去重" backend/src/main/java/com/xiyu/bid/tender/ --include="*.java"
```

---

## 完成后

```bash
WORKTREE=$(git rev-parse --show-toplevel)
echo '{"section":"4.2.1","phase":3,"phases_done":[1,2],"worktree":"'"$WORKTREE"'"}' > "$WORKTREE/.blueprint-checkpoint.json"

# 记录到记忆系统
SCRIPT_DIR=".claude/skills/blueprint-driven-development/scripts"
bash "$SCRIPT_DIR/memory-log.sh" append "4.2.1" "gap-analysis.md" "缺budget/deadline"
```
