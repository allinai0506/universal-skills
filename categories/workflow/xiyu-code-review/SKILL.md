---
name: xiyu-code-review
description: "按西域投标平台项目规范审查 PR 改动：架构边界（ArchUnit 11条规则）、安全配置、Design Token 一致性、Mock 残留检查、迁移合规性。当用户要求代码审查或 PR 审查时使用。"
---

# xiyu-code-review

按西域数智化投标管理平台项目规范审查代码改动。适用于 PR 审查或提交前的自审。

## 审查原则

1. **证据优先** — 每个 issue 都要给出具体文件:行号，不允许"可能有问题"
2. **分级处理** — Critical/Major 必须修复，Minor 建议修复，Info 供参考
3. **命令验证** — 所有规则都有对应的自动化验证命令，优先跑命令再读代码
4. **架构先行** — ArchUnit 违规是 CI 红线，必须在代码质量检查之前阻断

---

## 输出格式

每条 finding 必须包含：

```
[CRITICAL/Major/Minor/Info] <文件>:<行号>
  问题: <描述>
  原因: <为何违规>
  修复: <具体操作>
  命令: <验证命令（如果有）>
```

---

## 前置：获取改动范围

```bash
# 当前分支 vs main
git log origin/main..HEAD --oneline
git diff origin/main..HEAD --stat
```

---

## 1. 架构边界（ArchUnit — CI 红线）

运行 `ArchitectureTest.java` 中对应的 11 条规则，禁止只看文件 diff 而不跑测试。

### 1.1 Controller ↔ Repository 隔离

- **CRITICAL** 新模块（calendar, collaboration, competitionintel, scoreanalysis, roi, versionhistory, documenteditor, documentexport, documents, settings, fees, projectworkflow, resources, casework, analytics）的 Controller 是否直接依赖了 `..repository..`？
- **CRITICAL** auth/tender/batch/export/bidresult/approval 的 Controller 是否直接依赖了 `..repository..`？

```bash
cd backend && mvn test -Dtest=ArchitectureTest -q
# 或只看特定规则：
mvn test -Dtest=ArchitectureTest#strict_module_controller_should_not_depend_on_repository -q
```

### 1.2 Entity 纯净性

- **CRITICAL** 所有 Entity（带 `@Entity` / `@MappedSuperclass` 注解）是否依赖了 `..service..` 或 `..controller..`？
- **CRITICAL** JPA Entity 是否放置在 `domain/application/controller/service/repository` 包下？（必须在 `..entity..` 或 `..persistence.entity..`）

### 1.3 DTO 边界

- **CRITICAL** 新模块 Controller 是否直接返回了 Entity 类型？
- **CRITICAL** DTO 是否依赖了 `..service..`？
- **CRITICAL** 已完成 DTO 收口的模块（historyproject, settings, projectworkflow, analytics）的 DTO 是否继续依赖了 Entity？

### 1.4 Config 隔离

- **CRITICAL** `..config..` 包是否依赖了 `..service..`？（RULE 9）

### 1.5 循环依赖

- **CRITICAL** 新模块之间（calendar|collaboration|competitionintel|scoreanalysis|roi|versionhistory|documenteditor|documents）是否存在循环依赖？
- **CRITICAL** 任意两个模块 slice 之间是否存在循环？（排除 admin, ai, demo, platform, service, settings, batch, changetracking, mention, notification, casework, config, integration, tender, task, project, projectworkflow）

### 1.6 模块间依赖边界

- **MAJOR** `documentexport` 是否直接依赖了 `historyproject.repository` 或 `historyproject.entity`？（必须通过 `historyproject.application` / `dto` 访问）
- **MAJOR** `historyproject` 是否反向依赖了 `casework` / `documenteditor` / `documentexport` 内部实现？
- **MAJOR** `documenteditor` 是否依赖了 `historyproject` / `casework` / `documentexport`？

### 1.7 Util 工具类

- **MINOR** 带 `Util` / `Helper` 后缀的类是否依赖了 `..service..` 或 `..repository..`？

---

## 2. 安全配置

### 2.1 权限放大

- **CRITICAL** `SecurityConfig` 是否新增了放行路径（`/api/auth/sessions`、`/actuator/info`、`/h2-console/**`）？
- **CRITICAL** 新增的 `@GetMapping` / `@PostMapping` 端点是否都有权限注解？

### 2.2 密钥管理

- **CRITICAL** 生产代码中是否有硬编码的 JWT Secret、数据库密码、API Key？
- **CRITICAL** `.properties` / `.yml` 中是否有明文密码而非引用环境变量？

### 2.3 跨域与请求

- **MAJOR** CORS 配置是否指定了明确的 allowedOrigins（而非 `*`）？
- **MAJOR** 文件上传接口是否有大小限制和类型校验？

### 2.4 通用安全

通用检查参考 `security-review` 技能，重点检查：
- 输入校验（`@Valid`、`@NotNull`、`@Size` 等）
- SQL 注入（JPA `?` 参数化，禁止字符串拼接）
- XSS（用户输入写入响应前是否转义）
- 日志脱敏（用户敏感信息是否在日志中脱敏）

---

## 3. 前端规范（WeChat + Vue/React）

### 3.1 Design Token 一致性

- **MAJOR** CSS 中是否出现硬编码颜色（`#rgb`、`#rrggbb`）而未使用 CSS 变量（`var(--xxx)`）？
- **MAJOR** CSS 变量是否来自 `variables.css` / `tokens.css` 定义？
- **MINOR** 尺寸/间距是否使用 Design Token 而非硬编码数字？

```bash
# 颜色硬编码检测
rg '#([0-9a-fA-F]{3}){1,2}(?![[:alnum:]])' --type css -C 2 \
  | rg -v var\(
# 或在前端目录运行：
npm run lint:style
```

### 3.2 Mock / Demo 残留

- **MAJOR** 是否有 `isMockMode`、`demoPersistence`、`frontendDemo`、`USE_MOCK` 等标志导致生产代码走了 mock 分支？
- **MAJOR** `mock.js`、`mock-adapters/`、`__mocks__/` 是否还在被 import？
- **MINOR** `.env.mock` 或已删除配置的引用？

### 3.3 微信小程序特定

- **MAJOR** `wx.request` / `wx.connectSocket` 是否使用 HTTPS（生产环境）？
- **MAJOR** storage key 是否加项目前缀避免冲突？
- **MINOR** 是否在 `onShow` / `onLaunch` 中做了非必要的同步 storage 读写？

---

## 4. 数据库迁移（Flyway + MySQL 8.0）

### 4.1 版本与位置

- **CRITICAL** 迁移文件是否在 `src/main/resources/db/migration-mysql/` 目录？（不是废弃的 `migration/`）
- **CRITICAL** 版本号是否严格递增（大于当前最大版本）？
- **CRITICAL** 是否修改了已合入 main 的迁移文件？（已应用的迁移 checksum 不能变，修改 schema 必须创建新版本）

```bash
# 验证只有新文件被修改
git diff origin/main -- backend/src/main/resources/db/migration-mysql/ \
  | rg '^[+-][^-]' \
  | rg -v '^...' \
  | rg -v '^[+-]--' \
  | wc -l
# 如果 > 0，说明有旧文件被修改
```

### 4.2 MySQL 8.0 兼容性

- **CRITICAL** 是否使用了 H2 特有语法？（如 `VARCHAR_IGNORECASE`、`MODE=MySQL` 方言函数）
- **CRITICAL** 是否使用了 H2 保留关键字作为列名（`value`、`key`、`user`、`rank`、`groups` 等）？
- **CRITICAL** 多个 `VARCHAR(5000)` 以上的列是否会导致 MySQL 行大小超限（utf8mb4 下 65KB 上限）？超过时应使用 `TEXT` 类型。

### 4.3 增量字段

- **MAJOR** 新增 `@Version` 乐观锁字段时，迁移中是否包含 `ADD COLUMN version BIGINT NOT NULL DEFAULT 0`？
- **MAJOR** 新增非空字段时，迁移中是否有 `DEFAULT` 值或先允许 null 再 `UPDATE ... SET xxx = xxx DEFAULT` 再 `ALTER ... NOT NULL`？

### 4.4 锁表风险

- **MAJOR** `ALTER TABLE ... ADD COLUMN` 在 MySQL 8.0 online DDL 支持下通常安全，但涉及 `CHANGE COLUMN`、`DROP COLUMN`、添加有外键约束的列 时会锁表，是否评估过影响？
- **MINOR** 回滚脚本 `U{version}__{description}.sql` 是否存在且语法正确？

---

## 5. 代码质量

### 5.1 文件膨胀

- **MAJOR** 单文件行数是否超过 200 行（软上限）/ 300 行（硬上限）？
- **MAJOR** Controller / Application Service 中是否塞入了业务逻辑？（应下沉到 domain policy 或 service）

```bash
# 行数检查
rg '\.java$' --stats \
  | rg ':[0-9]{4,}' \
  | awk -F: '{print $1, $2}' \
  | sort -t' ' -k2 -rn \
  | head -20
```

### 5.2 返回值设计

- **MAJOR** `void` 方法是否隐藏了业务状态变化？（纯核心应返回值，void 只能在框架边界使用）
- **MINOR** `Optional` 是否正确使用（不用 `isPresent()` 判断后 `get()`，应用 `map()`/`flatMap()`/`orElseThrow()`）

### 5.3 日志规范

- **MINOR** 敏感字段（密码、token、手机号、身份证）是否在日志中脱敏？
- **MINOR** 错误日志是否包含足够上下文但不暴露内部实现细节？

### 5.4 测试覆盖

- **MAJOR** 新增的 service/policy 方法是否有对应的单元测试？
- **MINOR** 是否通过了 doc-governance 检查？

```bash
mvn test -q
# 或单独跑 doc-governance
npm run check:doc-governance
```

---

## 6. 构建验证

审查完成后，必须运行以下验证命令并截图结果：

```bash
# 后端：编译 + 架构测试
cd backend && mvn compile -q && mvn test -Dtest=ArchitectureTest -q

# 后端：全量测试
cd backend && mvn test -q

# 前端：编译检查
cd wechat-miniprogram && npm run build 2>&1 | tail -20

# 前端：代码规范
npm run lint --if-present
```

---

## 审查结论模板

```
## Code Review 结论

### 改动摘要
- 文件数: N
- 新增: N / 修改: N / 删除: N

### 严重问题（必须修复）
- [CRITICAL] ...

### 重要问题（建议修复）
- [MAJOR] ...

### 轻微问题（可选修复）
- [MINOR] ...

### 验证命令执行结果
- ArchUnit: PASS / FAIL（附截图）
- mvn test: PASS / FAIL（附截图）
- npm run build: PASS / FAIL（附截图）

### 最终结论
✅ 可合并 / ❌ 需修复后重审 / ⚠️ 需人工确认
```
