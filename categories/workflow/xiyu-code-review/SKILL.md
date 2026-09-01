***

name: xiyu-code-review
description: "按西域投标平台项目规范审查 PR 改动：三透镜审查（行为正确性/结构健康/交付就绪）、状态快照前置、架构边界（ArchUnit）、安全配置、Design Token 一致性、Mock 残留检查、迁移合规性。当用户要求代码审查或 PR 审查时使用。"
------------------------------------------------------------------------------------------------------------------------------------------

# xiyu-code-review

按西域数智化投标管理平台项目规范审查代码改动。适用于 PR 审查或提交前的自审。

> 本技能源自 PR !2399 四轮审查复盘（详见 `docs/lessons/lessons-learned.md` §154/§155）：
> 历次漏检集中在"行为正确性之外的平面"——依赖方向、全局常量影响面、交付就绪度。
> 因此本技能强制三透镜全覆盖，且任何一轮（含修复轮/复审轮）都从全量 diff 起步。

## 审查原则

1. **证据优先** — 每个 issue 都要给出具体文件:行号，不允许"可能有问题"
2. **分级处理** — Critical/Major 必须修复，Minor 建议修复，Info 供参考
3. **命令验证** — 所有规则都有对应的自动化验证命令，优先跑命令再读代码；**但自动化结果不得替代判断性结论**（见原则 8）
4. **架构先行** — ArchUnit 违规是 CI 红线，必须在代码质量检查之前阻断；**ArchUnit 全绿 ≠ 架构合理**（见 §7.1）
5. **全量 diff 原则** — 任何一轮审查（含修复轮/复审轮）必须从 `origin/main...branch` 全量 diff 起步；前轮 findings 清单只作附件、不作审查范围，防止清单继承盲区（PR !2399 教训：四轮审查全在行为平面，依赖方向/影响面/交付就绪从未进入检查面）
6. **三透镜独立否决** — 每个 PR 必须走完三透镜：A 行为正确性（代码对不对、测试够不够）/ B 结构健康（依赖方向、影响面、复杂度、耦合形态，见 §7）/ C 交付就绪（能不能合、卫生与契约，见 §8）。透镜 B 的发现不允许用"测试全绿"驳回，透镜 C 的发现不允许用"行为正确"驳回，各透镜有独立否决权；每轮报告必须声明"本轮新视角"
7. **审查独立性契约** — 派发 CodeReview 子代理时，prompt 中**禁止**包含修复意图、"本轮修了什么"、预期语义、"验证已通过"等作者解释；只允许给 diff 范围 + 项目标准 + 要回答的问题。让审查者从代码推断意图，而不是从作者嘴里接受意图（防确认偏误）
8. **判据分离** — 报告中"自动化结论"（ArchUnit/测试/lint 的 PASS/FAIL，命令证据）与"判断性结论"（依赖方向、影响面、复杂度、设计合理性，附推理文字）必须分栏陈述，禁止用前者顶替后者
9. **触发式专项审计** — 按 diff 特征强制触发对应深度审计（§9），触发即穷举、不得以"测试全绿"跳过：

   - 核心 Record/DTO 字段新增/修改 → §9.1 构造器调用点穷举 + 字段透传断言

   - 新增 Spring Bean / 提取策略 → §9.2 主链路挂载追查 + 三态降级测试

   - 新增/修改涉及入参或 getter 返回值的代码 → §9.3 逐行 Nullability 逆向攻击
     未触发不空跑（避免噪音），触发后属透镜 A 独立否决项，findings 走统一输出格式。

***

## 输出格式

每条 finding 必须包含：

```
[CRITICAL/Major/Minor/Info] <文件>:<行号>
  问题: <描述>
  原因: <为何违规>
  修复: <具体操作>
  命令: <验证命令（如果有）>
```

***

## 第 0 步：状态快照（审代码之前必做）

先拍 PR 状态快照再进入代码审查。**任一项异常即为交付阻塞项（透镜 C），写入报告的"合入前必做清单"**：

```bash
# 1. mergeable / 冲突状态（Gitee API；PR !2399 教训：四轮审查无人查 mergeable，合入时才发现冲突）
curl -s "https://gitee.com/api/v5/repos/<owner>/<repo>/pulls/<num>?access_token=$GITEE_TOKEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('mergeable:', d.get('mergeable'), '| head:', d['head']['sha'])"
# 本地等价检测（无 token 时）：
git merge-tree $(git merge-base origin/main <branch>) origin/main <branch> | grep -A3 "changed in both"

# 2. commit 结构与规模
git log origin/main..<branch> --oneline
git diff origin/main...<branch> --stat | tail -5

# 3. 空白行与格式异常（git diff --check 从源头拦截；命中 → 透镜 C 卫生阻塞项，写入"合入前必做清单"）
git diff --check origin/main...<branch>
# 命中项：trailing whitespace / space before tab / 新文件末尾缺换行（\ No newline at end of file）
# 判定：非空输出即异常，逐条列出文件:行号

# 4. 生成物/产物文件卫生（不应入库的笔记/产物文件被改动时标记，见 §8.3）
git diff --name-only origin/main...<branch> | grep -E '^(implementation-notes\.html|ui_mvp_preview\.html)$' || true

# 5. 跨语言关键词契约（改动触及契约两侧文件时执行）
node scripts/check-keyword-sync.mjs
```

***

## 前置：获取改动范围（全量优先）

```bash
# 当前分支 vs main（三点语义：分支独立改动）
git log origin/main..HEAD --oneline
git diff origin/main...HEAD --stat
```

- **修复轮/复审轮同样必须全量起步**——增量审查（只看上轮到本轮的改动）仅允许作为补充手段，不得作为唯一范围。

- 派发子代理时按"审查独立性契约"（审查原则 7）构造 prompt。

***

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

***

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

***

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

***

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

***

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

***

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

***

## 7. 结构健康（透镜 B — 不可用"测试全绿"驳回）

### 7.1 依赖方向与分层合理性（ArchUnit 绿 ≠ 方向合理）

- **MAJOR** 新增跨模块引用（尤其 domain→domain）时，必须在报告中给出方向选择的推理：

  - 反向引用是否会形成循环（`git grep "com.xiyu.bid.<对端模块>"` 查既有方向）？

  - 共享常量/类型放在哪一侧是最优解？有没有第三方共享位？

  - 该方向是否有既有先例（方向约定本身可能是历史决策，先例≠免审）？

- ArchUnit 只编码"禁止什么"，回答不了"这个位置/方向是否最优"——后者是判断题，必须附推理文字。

- **注意**：对"已被 wiki/lessons 正当化的历史决策"也要保留质疑权——先例是证据，不是豁免。

### 7.2 常量/全局参数影响面（命令模板，不靠自觉）

- **MAJOR** PR 改动任何 `static final` 常量、全局参数（如 `CONTEXT_AFTER_LINES`）、关键词表、阈值时，必须列出全部使用方并逐一评估非目标场景：

```bash
# 改动的常量/参数逐个跑：
git grep -n "<常量名>" -- backend/src/main/java
git grep -n "<常量名>" -- document-converter-sidecar src/
```

- 评估问题：该参数是否只影响目标场景？非目标场景（其他模块/其他业务路径）受不受影响？影响多大（如 token 消耗、召回率、误报率）？是否需要差异化策略（目标场景局部放宽、其余保持不变）？

### 7.3 复杂度与可读性（轻量判据，不引重型工具）

- **MAJOR** 单个方法分支点（`continue`/`break`/`return`/`throw` 合计）> 5 或嵌套 > 3 层 → 必须提出"提取方法"建议（如返回枚举 `KEEP/SKIP/PASSTHROUGH` 的分类方法）。

- **MAJOR** 循环体内含 3 个以上 `if-continue` 隐式编码的优先级判据 → 建议显式化（分类函数/策略表）。

- **MINOR** 魔法数哨兵值（如 `return -1000`）应提取为具名常量或改用 `Optional` 表达。

- **MINOR** 嵌套遍历消除算法（O(n²) `stream().noneMatch(...contains...)`）在数据增长前可读性优先：注释写清"保留不被更长词包含的词"语义。

- **MINOR** 多个常量词表高度重叠（>50% 交集）时，要求 Javadoc 明确各自职责边界，或用组合/差集定义消除重复。

### 7.4 "两层互救"反模式检测（PR !2399 教训）

- **MAJOR** A 层"跳过/过滤"、B 层"守卫抢救"的耦合结构必须标出：正则判跳过 + 提取器守卫捞回、拦截器丢弃 + 下游重试兜底等。特征：注释中出现"已知误杀面""兼容保留""由 X 侧守卫保留"字样。

- 要求：优先在单层内消除误杀（收窄判据）；确需两层协作时，两端必须各有锚定测试，且在两处代码注释中互相指向。

- **MINOR** 同一文件内风格改动（for→stream、多行→单行）与功能改动混排（特征：大行数变动但净增 ≈ 0）→ 建议拆独立 commit。

- **MINOR** 跨语言/跨进程契约（Java ↔ Python 关键词表等）若仅靠注释约束 → **MAJOR**，必须有自动化校验（如 `scripts/check-keyword-sync.mjs`）。

***

## 8. 交付就绪（透镜 C — 不可用"行为正确"驳回）

### 8.1 合入状态硬清单（第 0 步快照异常项在此收口）

- **CRITICAL** `mergeable: false` → 阻断合入，提示 rebase 并列出冲突文件（`git merge-tree` 定位）。

- **CRITICAL** CI 未通过 / 未跑完 → 阻断。

- **MAJOR** PR body 项目复选框（知识沉淀 / wiki 回填 / 测试证据）未勾选且对应改动缺失。

- 工具：`scripts/gitee-pr-helper.sh check <num>`（打印 mergeable）；`scripts/gitee-pr-helper.sh merge <num>` 合入前会强制断言 `mergeable=true`（逃生阀 `GITEE_PR_FORCE_MERGE=1`）。

### 8.2 commit 卫生

- **MINOR** 风格改动与功能改动混在同一 commit（见 §7.4 特征）。

- **MINOR** commit 数量与改动规模不匹配（单个巨型 commit 无法分域审查）。

- **MINOR** 误用旧提交消息（`git commit -C` 复用）→ 检查最新 commit message 与实际改动匹配。

### 8.3 仓库卫生

- **MAJOR** 生成物/笔记类文件（`implementation-notes.html`、`ui_mvp_preview.html` 等）被改动或新增入库 → 提示迁移到 `docs/` 或加入 `.gitignore`。

- **MINOR** 根目录新增游离 `*.md` 笔记（应进 `docs/` 对应目录，见知识沉淀纪律）。

- **MINOR** 追踪的符号链接/文件被本地删除（会挡住 rebase）→ `git checkout -- <path>` 恢复。

### 8.4 跨语言契约自动化（§7.4 的工程化配套）

```bash
node scripts/check-keyword-sync.mjs
# 契约两侧（Java PriceScoringKeywords ↔ Python converter.py 关键词元组）不一致即失败；
# 仅一侧存在（单边新增契约）同样失败，防"加了 Java 忘加 Python"的静默回退。
```

***

## 9. 专项深度审计（透镜 A — 按 diff 特征触发，见审查原则 9）

> 本节为触发式审计：未命中触发条件不空跑，命中则**强制穷举**，不得以"测试全绿 / 自动化通过"跳过。
> 触发条件在 §9 每小节标注，扫 diff 时逐条比对。

### 9.1 Record/DTO 字段增改透传审计

**触发条件**：diff 中新增、重命名或修改了核心领域 Record / DTO / Entity 的字段（含 record 组件字段、getter/setter、`@JsonProperty` 别名）。

**强制动作**：穷举该类型所有构造器调用点与映射点，断言每个中转管道正确传播新字段。

```bash
# 1. 穷举所有构造器调用点（含 record 的紧凑/规范构造、new XxxRecord(...)）
git grep -n "new <RecordName>(" -- backend/src/main/java
# 2. 穷举 DTO ↔ Entity ↔ Record 的映射/转换方法（含 copyProperties、手动 setter）
git grep -n "<RecordName>" -- backend/src/main/java | rg -i 'copy|convert|toDto|toEntity|of\(|from\('
# 3. 若使用 MapStruct / BeanUtils，核对字段声明两侧是否同步
```

**逐点断言**（每个调用点都必须回答）：

- **构造参数漏传** — 新字段是否在所有 `new XxxRecord(...)` 调用点被显式传入？漏传处是传 null/默认值还是编译错误？（record 固定位置构造参数漏传会**静默错位**：字段值被挪到相邻字段）

- **命名位置记录** — record 是无参名构造的，新增字段插在中间会整体错位，必须比对每个调用点的参数顺序。

- **映射管道缺口** — 含 `BeanUtils.copyProperties` / MapStruct 的转换点，检查源/目标两侧是否都声明了新字段；只加一侧导致新字段在管道中丢失。

- **序列化边界** — 新字段是否影响 JSON 序列化（@JsonProperty 别名、@JsonIgnore、feign/DTO 跨服务契约）？对外 DTO 增字段是**兼容变更**，删除/改名是**破坏变更**，需确认下游消费者。

- **持久化边界** — Entity 增字段是否配套 Flyway 迁移（见 §4.3）？查询投影（JPQL constructor expression、interface projection）是否缺该字段？

**判定**：任一调用点漏传/错位/映射缺口 → **CRITICAL**（静默 null/错位数据），写清文件:行号与影响路径。

### 9.2 新组件挂载与三态降级审计

**触发条件**：diff 新增 Spring Bean（`@Component` / `@Service` / `@Repository` / `@Configuration` 中的 `@Bean`）或提取出新的策略/接口实现。

**强制动作**：

```bash
# 1. 追查主链路调用点：确认新 Bean 真正被挂到了主业务流程，而非"定义了但无人调用"的孤儿 Bean
git grep -n "<新Bean类名>" -- backend/src/main/java
#   注入点（@Autowired / 构造器注入 / Optional<List<T>> / Map<String, T>）必须出现在实际调用链上
# 2. 三态测试清点
git grep -n "class .*Test" -- backend/src/test | rg -i "<新Bean|策略接口名>"
```

**三态降级断言**（对"是否参与主链路"的可选/策略组件，强制要求三类证据，缺一类即 **MAJOR**）：

- **有 Bean 正常** — 存在至少一个该 Bean 生效的路径测试（happy path 集成/单元测试）。

- **无 Bean 降级** — 组件缺失（`@ConditionalOnMissingBean` / 接口无实现 / `Optional<T>` 注入为空）时，主链路行为有明确 fallback 且被测试覆盖；若"无 Bean 直接失败"是既定设计，必须写明依据。

- **抛异常降级** — 组件抛异常时不拖垮主链路：有 try-catch 兜底、降级返回值或熔断，且该路径有测试/明确证据；禁止"组件异常 = 主链路 500"且无兜底说明。

**补充检查**：

- 提取策略时，接口是否有多实现；多实现选型（`@Primary` / `@Qualifier` / `Map<String, T>` 按 key）在运行期是否能被正确解析，缺失解析是否会抛 `NoSuchBeanDefinitionException`。

- 新 Bean 的创建是否可能在主链路启动/首次调用时抛异常（构造器内做 IO、读外部配置无默认值）。

**判定**：孤儿 Bean（无主链路调用点）→ **MAJOR**；三态缺类且无依据 → **MAJOR**；构造器有未兜底异常风险 → **CRITICAL**。

### 9.3 逐行 Nullability 逆向攻击

**触发条件**：diff 新增/修改了含入参或 getter 返回值调用的代码（服务方法、策略方法、DTO 转换、工具类）。

**强制动作**：对 diff 中**每一个**入参和 getter 返回值，**默认假设其为 null**，逐行检查是否直接调用了可能 NPE 的方法，逐个给出文件:行号。

**攻击清单**（命中任一项 → **CRITICAL**，除非该值在链路上有可见的 @NotNull / Objects.requireNonNull 前置保证）：

- **包装类型拆箱** — `Boolean` 直接 `if (flag)`、`Integer` 参与算术、`Long` 比较 → 拆箱 NPE；应 `Boolean.TRUE.equals(flag)` 或判空。

- **Optional 直接取值** — `.get()` 未先 `isPresent()` / `orElseThrow()`；应改用 `map()` / `flatMap()` / `orElse(default)`。

- **String 未判空即操作** — `.length()`、`.substring()`、`.trim()`、`.toLowerCase()`、以 receiver 身份调用 `.equals(x)`（null 时 NPE；应将已知常量放左侧 `"x".equals(v)` 或 `Objects.equals`）。

- **集合/数组未判大小** — `.get(0)` / `list[0]` / `.getFirst()` 未确认非空且非空集合；迭代前未判 null。

- **getter 链式穿透** — `a.getB().getC().getD()` 中间节点无判空；应逐步判空或使用 Optional 链。

- **方法返回值信任** — 对 `findById()` / `findByXxx()` / `getXxx()` 返回值直接解引用，未处理"不存在"分支（应 `orElseThrow` / 判空降级）。

**命令辅助**（静态工具可辅助，但结论必须人工核对，不得仅凭工具）：

```bash
# 在 diff 范围内粗筛高风险调用（结果需人工逐条核对，工具不产生最终结论）
git diff origin/main...<branch> -- backend/src/main/java | rg -nE '\.get\(\)|\.length\(\)|\.substring\(|\.getFirst\(|\.get\(0\)|if\s*\([a-zA-Z_$][\w$]*\)\s*\{'
```

**判定**：确认 NPE 风险且链路上无前置保证 → **CRITICAL**；有前置保证但未显式声明（依赖隐式约定）→ **MAJOR**（建议显式化）。

***

## 审查结论模板

```
## Code Review 结论

### 状态快照（第 0 步）
- mergeable: true / false（冲突文件: ...）
- commits: N | 文件数: N | +N / -N
- git diff --check: 通过 / 异常（列出文件:行号）
- 生成物文件卫生: 通过 / 异常（列出）
- 跨语言契约检查: 通过 / 失败 / 不适用（未触及契约文件）
- 专项深度审计触发: §9.1 / §9.2 / §9.3 / 无触发（触发项必须给出穷举结果）
- 本轮新视角: <本轮看了哪些上轮没看的维度>

### 改动摘要
- 新增: N / 修改: N / 删除: N

### 严重问题（必须修复）
- [CRITICAL] ...（标注所属透镜 A/B/C 及 §9.x 触发项，如有）

### 重要问题（建议修复）
- [MAJOR] ...（标注所属透镜 A/B/C 及 §9.x 触发项，如有）

### 轻微问题（可选修复）
- [MINOR] ...（标注所属透镜 A/B/C 及 §9.x 触发项，如有）

### 自动化结论（命令证据）
- ArchUnit: PASS / FAIL（附输出）
- mvn test: PASS / FAIL（附输出）
- npm run build: PASS / FAIL（附输出）
- check-keyword-sync: PASS / FAIL / N/A
- git diff --check: PASS / FAIL（附输出）

### 判断性结论（附推理，不得用自动化结果顶替）
- 依赖方向: ...
- 影响面: ...
- 复杂度: ...
- 设计合理性: ...

### 重新设计建议（必填，允许"无"，不允许跳过——对抗补丁式收敛）
- ...

### 合入前必做清单（透镜 C）
- [ ] ...

### 最终结论
✅ 可合并 / ❌ 需修复后重审 / ⚠️ 需人工确认
```

