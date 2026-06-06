# Phase 2 差距分析参考示例

> 本文档是 Phase 2 的配套参考手册，提供真实场景示例。
> 适用于：当需要判断某个功能是否"已实现"时，对照本文档的示例。

## 核心判断原则

### 什么算"已实现"

**后端 API**：
- ✅ Controller 存在且 `@GetMapping` / `@PostMapping` 标注正确
- ✅ DTO 字段与蓝图对齐（字段名完全一致、类型正确、约束正确）
- ✅ Service 层有对应业务逻辑
- ✅ Repository 存在

**前端 UI**：
- ✅ 页面/组件存在
- ✅ 表单字段与蓝图完全对齐
- ✅ v-permission / v-if 权限指令与蓝图权限矩阵一致
- ✅ API 调用正确（URL、参数、返回值处理）

**数据库**：
- ✅ 表存在
- ✅ 字段存在（名字、类型、约束）
- ✅ 索引完整

### 什么算"未实现"

- ❌ 接口不存在
- ❌ DTO 字段缺失或类型不对（`String` vs `BigDecimal`）
- ❌ 前端组件存在但字段绑定不完整
- ❌ 权限指令缺失或与蓝图矛盾
- ❌ 业务流程缺少步骤（蓝图 A→B→C，实际只有 A→C）

### 最容易误判的三种情况

| 误判类型 | 实际情况 | 正确判断 |
|---------|---------|---------|
| "有类似字段就算实现" | 蓝图要求 `DECIMAL(15,2)` 预算字段，现有 `String budget` | ❌ 未实现，类型不一致 |
| "前端有组件就算实现" | 蓝图要求"提交→审核"两阶段，前端有提交按钮但无审核流程 | ❌ 未实现，流程不完整 |
| "字段名对就算实现" | 蓝图要求 `review_status`，代码中 `reviewStatus` 是 `Boolean` 而非 `Enum` | ❌ 未实现，类型不对 |

---

## 真实示例：§3.3.1.6 项目结项

以下示例展示真实的差距分析过程（来自实际代码审查）。

### 示例 1：完整实现判断

**蓝图要求**：
> 项目结项 → 保证金退回 → 状态为"未退回"时显示文字提示

**验证过程**：
```bash
# 后端
grep -rn "depositReturned\|deposit_returned" \
  backend/src/main/java/com/xiyu/bid/project/entity/ \
  --include="*.java"
# 结果：ProjectClosure.java 第 34 行有 `private Boolean depositReturned;` ✅

# 前端
grep -rn "depositReturned\|未退回" \
  src/views/Project/stages/ClosureStage.vue \
  --include="*.vue"
# 结果：第 67 行有 `v-if="!depositReturned"` ✅

# 结论：已完整实现
```

**gap-analysis 写法**：
```
| 保证金未退回文字提示 | UI | depositReturned=false 时显示"未退回" | 已实现 ✅ |
```

### 示例 2：类型不一致（误判风险高）

**蓝图要求**：
> 项目预算字段：DECIMAL(15,2)，单位万元

**验证过程**：
```bash
# 检查实体字段类型
grep -rn "budget\|项目预算\|projectBudget" \
  backend/src/main/java/com/xiyu/bid/project/entity/ \
  --include="*.java" -B 1 -A 1

# 实际结果：
# ProjectInitiationDetails.java 第 45 行：
#   private String budget;  ← 是 String，不是 BigDecimal！

# 检查前端类型
grep -rn "budget" \
  src/views/Project/stages/InitiationStage.vue \
  --include="*.vue" -B 1 -A 1

# 实际结果：
# 第 123 行：<el-input-number v-model="form.budget">
# → 前端用 el-input-number，说明预期是数字类型
```

**gap-analysis 写法**：
```
| 项目预算字段类型 | 数据库/后端 | 蓝图要求 DECIMAL(15,2) | 当前 ProjectInitiationDetails.budget 是 String，类型不一致 | M（需修改实体 + 迁移 + 前端绑定） |
```

### 示例 3：业务流程缺失

**蓝图要求**：
> 项目结项流程：项目负责人提交结项 → 投标团队审核 → 通过/驳回

**验证过程**：
```bash
# 步骤 1：检查提交接口
grep -rn "submit.*closure\|closure.*submit" \
  backend/src/main/java/com/xiyu/bid/project/ \
  --include="*.java" -i
# 结果：ProjectClosureService.submit() 存在 ✅

# 步骤 2：检查是否有审核接口
grep -rn "approve.*closure\|reject.*closure\|审核" \
  backend/src/main/java/com/xiyu/bid/project/ \
  --include="*.java" -i
# 结果：无相关代码 ❌

# 步骤 3：检查数据库是否有审核状态字段
grep -rn "review_status\|review_status" \
  backend/src/main/resources/db/migration-mysql/V*.sql
# 结果：V128 有 review_status 字段 ✅

# 步骤 4：检查前端审核按钮
grep -rn "审核\|approve\|reject" \
  src/views/Project/stages/ClosureStage.vue \
  --include="*.vue"
# 结果：无审核按钮 ❌

# 结论：审核流程未实现，数据库字段存在但未被使用
```

**gap-analysis 写法**：
```
| 结项审核流程 | 业务流程 | 蓝图要求：提交→审核→通过/驳回 | 当前仅有 submit，无 approve/reject 接口和 UI | L |
| review_status 字段使用 | 数据库/后端 | review_status 应由审核操作填充 | 字段存在于 V128 但 submit 和审核 Service 均未写入 | M |
```

---

## 真实示例：动态表单引擎 (§3.4.X)

### 示例 4：字段级对齐验证

**蓝图要求**：
> 表单字段定义：
> - `fieldKey`: VARCHAR(64)，唯一标识
> - `fieldType`: ENUM('TEXT','NUMBER','DATE','SELECT'...)
> - `required`: BOOLEAN
> - `label`: VARCHAR(128)

**验证过程**：
```bash
# 步骤 1：检查数据库表
grep -rn "CREATE TABLE.*form_field\|CREATE TABLE.*form_definition" \
  backend/src/main/resources/db/migration-mysql/V*.sql
# 结果：V140__form_definition_schema.sql 存在 ✅

# 步骤 2：检查字段定义实体
grep -rn "class FormFieldDefinition\|record FormFieldDefinition" \
  backend/src/main/java/com/xiyu/bid/formengine/ \
  --include="*.java" -A 20
# 结果：存在，字段有 key/type/required/label ✅

# 步骤 3：检查 fieldType 枚举值（⚠️ 必须逐个验证）
grep -rn "TEXT\|NUMBER\|DATE\|SELECT\|FILE" \
  backend/src/main/java/com/xiyu/bid/formengine/domain/FormFieldType.java \
  --include="*.java"
# 结果：枚举值完整 ✅

# 步骤 4：前端渲染器对齐
grep -rn "fieldType\|field\.type" \
  src/views/System/DynamicFormRenderer.vue \
  --include="*.vue"
# 结果：有 switch(field.type) 渲染逻辑 ✅
# 但发现：FILE 类型有渲染但无上传逻辑 ❌
```

**gap-analysis 写法**：
```
| fieldType 枚举值 | 后端/前端 | 蓝图要求 TEXT/NUMBER/DATE/SELECT/FILE... | FormFieldType 枚举值完整 ✅，前端渲染器有对应 case ✅ | 0 |
| FILE 字段上传 | 前端/后端 | FILE 类型需支持上传和存储 | 前端有 FILE 渲染 case 但无上传 API 调用 | M |
```

---

## 字段级验证命令速查

### 验证 DTO 字段（后端）

```bash
# 查看 DTO 的完整字段声明
grep -rn "class.*Request\|record.*Request" backend/src/main/java/com/xiyu/bid/<module>/dto/ --include="*.java" -A 30 | grep "private\|public"

# 验证特定字段
grep -rn "private.*budget\|private.*status\|private.*deadline" backend/src/main/java/com/xiyu/bid/<module>/ --include="*.java"

# 验证枚举类型
grep -rn "enum.*Status\|Status.*enum" backend/src/main/java/com/xiyu/bid/<module>/ --include="*.java" -A 20
```

### 验证前端表单字段

```bash
# 查看表单字段绑定
grep -rn "v-model\|\:model-value\|:value" src/views/<module>/ --include="*.vue" | grep "form\.\|model\." | head -30

# 验证下拉选项
grep -rn "el-select\|el-option" src/views/<module>/ --include="*.vue" -B 1 -A 1 | head -40

# 验证权限指令
grep -rn "v-permission\|v-if.*role\|v-if.*admin" src/views/<module>/ --include="*.vue" | head -20
```

### 验证数据库字段

```bash
# 查看最近迁移中的表定义
grep -rn "CREATE TABLE\|ADD COLUMN" backend/src/main/resources/db/migration-mysql/V*.sql | grep -i "<table_name>"

# 验证字段类型
grep -rn "budget\|status\|deadline" backend/src/main/resources/db/migration-mysql/V*.sql | grep -i "<table_name>" | tail -10

# 验证枚举约束
grep -rn "ENUM\|CHECK.*IN\|VARCHAR.*DEFAULT" backend/src/main/resources/db/migration-mysql/V*.sql | grep -i "<table_name>" | tail -5
```

---

## 快速自检清单

在写入 gap-analysis.md 之前，逐项确认：

- [ ] 蓝图每个字段 → 对应的 DTO 字段存在
- [ ] DTO 字段类型 → 与蓝图要求一致
- [ ] 前端表单字段 → 与蓝图完全对齐
- [ ] 每个按钮/操作 → 权限指令正确
- [ ] 业务流程每个步骤 → 有对应的接口/UI
- [ ] 每个新增字段 → 有 Flyway 迁移脚本
- [ ] 每个权限变更 → 有对应的菜单权限配置

---

## 常见"已实现"陷阱

### 陷阱 1：只 grep 字段名，不验证类型

```bash
# ❌ 错误：只检查字段名存在
grep -rn "budget" backend/src/main/java/com/xiyu/bid/project/dto/
# 匹配到 String budget 和 BigDecimal budget —— 误判为已实现

# ✅ 正确：检查完整声明
grep -rn "private.*budget" backend/src/main/java/com/xiyu/bid/project/dto/ --include="*.java" -A 0
# 看到 private String budget ← 实际与蓝图 DECIMAL 要求不一致
```

### 陷阱 2：前端有组件，后端是 placeholder

```bash
# 前端
grep -rn "handleSubmit\|onSubmit" src/views/Project/stages/ClosureStage.vue --include="*.vue"
# 结果：第 89 行有 handleSubmit 方法 ✅

# 后端
grep -rn "handleSubmit\|closureSubmit" backend/src/main/java/com/xiyu/bid/project/ --include="*.java"
# 结果：只有 log.info("submit") —— 实际只是打印日志，没有持久化 ❌

# 正确做法：前后端必须同时验证
```

### 陷阱 3：状态枚举值不完整

```bash
# 检查枚举
grep -rn "enum.*DepositReturnStatus" backend/src/main/java/com/xiyu/bid/project/ --include="*.java" -A 15
# 结果：
#   NOT_RETURNED,   // 0 - 未退回
#   RETURNED        // 1 - 全部退回

# 蓝图要求：NOT_RETURNED / ALL_RETURNED / PARTIAL_RETURNED / TRANSFERRED
# 实际只有 2 个状态，蓝图要求 4 个 → ❌ 未完整实现
```

### 陷阱 4：权限写在代码里，没有配菜单权限

```bash
# 前端有 v-permission
grep -rn "v-permission.*closure\|v-permission.*approve" src/views/Project/ --include="*.vue"
# 结果：存在 ✅

# 但没有在数据库里配置
grep -rn "INSERT.*menu_permissions\|menu_permission" \
  backend/src/main/resources/db/migration-mysql/V*.sql | grep -i "closure\|approve"
# 结果：无相关 INSERT → ❌ 权限未生效
```

---

---

## 对比案例：旧版 vs 改进版差距分析

以下案例来自 §3.3.1.6 项目结项，展示了改进前后 Phase 2 的输出差异。

### 案例：保证金退回状态

**蓝图要求**：4 种状态（未退回/全部退回/部分退回+转服务费/全部转服务费）

**旧版差距分析**（错误）：
> "仅 boolean depositReturned，3 状态（NA/NOT_RETURNED/RETURNED）"

**验证过程**（改进版）：
```bash
$ grep -rn "enum.*DepositReturnStatus" backend/src/main/java/com/xiyu/bid/project/core/ -A 15
# 结果：实际有 5 个枚举值
# NOT_RETURNED
# FULLY_RETURNED
# TRANSFERRED_TO_FEE
# PARTIAL_RETURN_PARTIAL_TRANSFER
# NA
```

**gap-analysis 结论**：✅ **已实现**（5 状态 > 蓝图要求 4 状态）

**旧版写的是**：❌ 未实现，需"扩展枚举"

**为什么会错**：Agent 只读 commit message 写了"3 状态"，没实际 grep 代码

---

### 案例：审核流程

**旧版差距分析**（错误）：
> "直接结项，无审核流程"

**验证过程**（改进版）：
```bash
$ grep -rn "@PostMapping" backend/src/main/java/com/xiyu/bid/project/controller/ProjectClosureController.java
# 结果：
# 第 50 行：@PostMapping          (submit)
# 第 67 行：@PostMapping("/approve")  ← 审核通过
# 第 78 行：@PostMapping("/reject")    ← 审核拒绝
```

**gap-analysis 结论**：✅ **审核接口已实现**（approve + reject）

**前端验证**：
```bash
$ grep -rn "approve\|审核\|reject" src/views/Project/stages/ClosureStage.vue
# 结果：第 204-249 行有完整的审核通过/拒绝 UI
```

**旧版写的是**：❌ 未实现，需"submit→approve/reject 分离"

**为什么会错**：Agent 没 grep 实际的 Controller 代码，只看 commit history

---

### 案例：V128 字段

**旧版差距分析**：
> "缺 V128 字段（review_status, reviewed_by, reviewed_at, project_summary）"

**验证过程**（改进版）：
```bash
$ grep -rn "review_status\|reviewed_by\|projectSummary" \
  backend/src/main/java/com/xiyu/bid/project/entity/ProjectClosure.java
# 结果：
# 第 40 行：private String depositReturnStatus;
# 第 83 行：private String projectSummary;   ← 存在
# 第 88 行：private Long reviewedBy;          ← 存在
# 第 91 行：private LocalDateTime reviewedAt; ← 存在
```

**gap-analysis 结论**：✅ **字段已存在**

**旧版写的是**：❌ "缺 review_status 等 4 个字段"

**为什么会错**：Agent 用了过期的 gap-analysis（基于 2026-06-03 的状态），没有重新验证

---

## 输出格式模板

gap-analysis.md 的标准格式（可直接复制）：

```markdown
# 差距分析 - §X.X.X [小节标题]

**分析时间**: YYYY-MM-DD
**分析范围**: [小节标题]
**蓝图文件**: [飞书文档链接]

---

## 蓝图要求清单

| # | 功能点 | 类型 | 蓝图描述 |
|---|--------|------|---------|
| 1 | [功能名] | [后端API/前端UI/业务流程/数据库/权限] | [蓝图原文描述] |
| 2 | ... | ... | ... |

---

## 逐项验证

### #N [功能点名称]

**蓝图要求**: [完整引用]

**验证过程**:
```bash
# 验证命令
$ grep -rn "..." ...
# 结果：[实际输出]
```

**gap-analysis 写法**: [结论 + 依据]

---

## 汇总

| # | 功能点 | 验证结论 | 工作量 | 本次做 |
|---|--------|---------|--------|--------|
| N | [功能名] | [✅ 已实现 / ❌ 未实现 / ⚠️ 部分实现] | [S/M/L] | [✅/—] |

**本次不做**（需明确写原因）:
1. [功能名] — 原因：依赖 X 模块
2. [功能名] — 原因：蓝图表述待产品确认
```
