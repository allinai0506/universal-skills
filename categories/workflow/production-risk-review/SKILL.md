---
name: production-risk-review
description: "对已上线系统的 PR 执行生产风险审计（Production Risk Review v2.0），目标是证明不存在足以导致线上回归的风险，而非证明代码正确。触发词：生产风险审计、上线后 PR 审查、风险审计、PR 能不能上线、审计这个 PR。当项目已上线、用户要求审查 PR 是否可上线时必须使用，替代普通 Code Review。"
---

# Production Risk Review v2.0

> **目标不是证明代码正确。**
> **目标是证明：即使上线，也尽可能不会出现 Bug 回归。**

## 核心原则

1. **默认存在 Bug**，不要假设开发者是正确的
2. **不要停留在修改代码本身**，持续扩展分析所有依赖和影响范围
3. **任何"没有问题"都必须提供代码证据**（文件:行号），禁止无依据判断
4. **模拟真实生产环境**，包括高并发、异常、故障和边界数据
5. **只有当所有风险都被证伪后，才能给出 PASS；否则一律 FAIL**

一句话：

> 不是寻找 Bug，而是系统性证明"不存在足以导致线上回归的风险"。

---

## 前置：获取改动范围

```bash
# NexusArchive 基线分支是 dev（main 已删除）
git fetch origin
git log origin/dev..HEAD --oneline
git diff origin/dev..HEAD --stat
git diff origin/dev..HEAD
```

或通过 Gitee MCP 获取 PR diff：`get_pull_detail` + `get_diff_files`。

---

## 第一阶段：理解（不要急着看代码）

审计第一件事不是 Review，而是回答：**这个 PR 到底改变了什么？**

必须输出下表（每项无改动也要显式写"无"）：

| 项目       | 内容 |
| ---------- | ---- |
| 修改目的   |      |
| 修改模块   |      |
| 修改流程   |      |
| 修改数据库 |      |
| 修改缓存   |      |
| 修改接口   |      |
| 修改配置   |      |
| 修改权限   |      |
| 修改第三方 |      |

然后继续问：**真正受影响的地方有哪些？**

不是"修改了 UserService"，而是"所有调用 UserService 的地方"。必须画调用链：

```
Controller → Service → Domain → Repository → MySQL → Redis → MQ → 第三方
```

任何节点都不能遗漏。用 Grep/SearchCodebase 找出每个改动符号的全部调用方，不允许只读 diff。

---

## 第二阶段：影响分析（Dependency Expansion）

这是整个审计最重要的一步。不断问自己：

```
如果这里变了，还有谁依赖它？
```

示例推演：

```
改了 DTO
  → 谁引用 DTO？
  → 有没有旧接口？
  → 有没有前端页面/小程序？
  → 有没有 SDK/对接方（泛微OA、NCC、福寿康）？
  → 有没有导出（Excel/PDF）？
  → 有没有报表/统计（dashboardStats）？
```

**直到没有新的影响为止。**

不要只 Review 代码，Review 依赖。

NexusArchive 特定扩散点（必须逐一检查）：

- 归档链路 ID（批次/凭证/文件 ID）必须保持 `String`，禁止改 `Long`
- `sys_doc_field_definition` 配置驱动的单据解析逻辑，接口 `/api/v1/integration/documents` 按 `sourceSystem` 复用
- 全宗隔离：`fonds_code` / `X-Fonds-No` / `FondsContext` 相关改动必须检查跨全宗数据泄漏
- Redis 缓存 key 维度变更（dashboardStats、groupedFonds、fondsScope）必须评估旧缓存失效
- Flyway 迁移：禁止修改已发布文件（checksum 红线），只能新增版本
- 8 个保留字段（voucherType, businessDate, amount, counterparty, summary, sourceSystem, fondsCode, fiscalYear）禁止在 displayFields 中重配

---

## 第三阶段：Bug 推演（Reverse Thinking）

不要问"有没有 Bug"，应该问：

```
如果线上炸了，最可能为什么？
```

然后持续问"为什么"直到根因。示例：

```
数据库锁死
  为什么？← SQL 变慢
  为什么？← 索引失效
  为什么？← 新增 OR 条件
```

对本次改动至少做 3 条独立的故障推演链，每条推演到根因并给出证伪/证实证据。

---

## 第四阶段：Bug 分类检查（固定 Checklist）

不要想到什么查什么。逐项过以下清单，每项给出 PASS/FAIL + 证据：

### 空值
- null / Optional / Empty List / Empty String / `Map.get()` 返回值未判空

### 集合
- ConcurrentModification / 越界 Index / Iterator 删除 / Stream 关闭 / parallelStream 线程安全

### 并发
- 锁粒度与死锁 / CAS ABA / volatile 误用 / ThreadLocal 未清理 / Future 未处理异常 / 线程池耗尽（禁止把 webhook 等 IO 任务塞进 `pdfGenerationExecutor` 这类 CPU 池，必须用 `taskExecutor`）

### 数据库
- 事务边界（多表写入是否同一事务）/ 回滚完整性 / 索引覆盖 / 行锁与死锁 / 慢 SQL / 深分页 / N+1
- 涉及多表写入的 API/Service 必须过 RELIABILITY.md 写操作规范检查清单

### Redis
- 缓存穿透 / 击穿 / 雪崩 / TTL 合理性 / 缓存与 DB 一致性 / 缓存 key 是否含全宗维度（防跨全宗泄漏）

### MQ / 异步
- 重复消费 / 消息丢失 / 顺序性 / 幂等设计

### API 兼容
- 字段删除 / 字段新增（旧客户端是否兼容）/ 字段类型变更 / 默认值变更 / 对接方（泛微OA、NCC）契约是否破坏

### JSON
- 序列化/反序列化对称 / 枚举映射 / 日期格式（JacksonTypeHandler 已注册 JavaTimeModule）/ Long 精度（前端 JS 丢失）/ BigDecimal

### 时间
- UTC / 时区 / DST / LocalDateTime 序列化

### IO
- 文件/Stream/连接是否关闭（try-with-resources）

### 前端（如涉及）
- 权限点精确性（禁止宽 OR 条件，用 computed + every()）/ `react-hooks/exhaustive-deps` / useCallback 包裹 props 函数 / Zustand 精确 selector

### 存量数据兼容
- 新代码对存量生产数据的假设是否成立（字段 null、旧枚举值、旧格式 JSON、历史脏数据）
- Schema/字段语义变更是否需要数据订正脚本；订正脚本是否幂等
- 新增非空约束前，存量数据是否已回填

### 测试与验证证据
- 关键修复/新逻辑是否有对应单元测试或回归测试（缺失即 P1）
- 已执行 CLAUDE.md 最少验证命令并附输出：前端改动 `npm run lint` + `npm run test:run`；路由/边界/模块改动补 `npm run check:arch` + `npm run modules:validate`；后端改动 `npm run backend:test`
- 验证命令未执行时，对应检查项不得判 PASS

---

## 第五阶段：业务回归检查

不要只检查代码，检查业务。沿业务链逐环验证：

```
修改了凭证归档
  → 预归档池还能不能看？
  → 归档流程还能不能走完？
  → 检索/全景视图还能不能查？
  → PDF 生成还能不能跑？
  → 导出还能不能用？
  → 各角色权限视图是否正常？
```

所有受影响业务链全部列出并逐环给出验证证据。

---

## 第六阶段：极端场景模拟

主动模拟并回答"系统会不会崩"：

- Redis 挂掉 / 数据库慢 / MQ 积压 / 服务器重启 / 网络超时 / 第三方失败
- 用户连续点击 / 重复提交 / 高并发
- 百万数据 / 空数据 / 异常数据 / 非法参数 / 权限不足

每个场景给出：系统行为推演 + 代码证据（降级、重试、幂等、校验在哪一行）。

---

## 第七阶段：反向寻找隐藏 Bug

不要 Review 代码，Review 作者。假设开发经验只有 2 年，他最容易犯哪些错：

- 事务忘了 / 异常吞了（catch 后只 log 不抛）/ finally 漏了
- 缓存没删 / 分页没加 / SQL 没索引 / ThreadLocal 没清
- 权限注解漏加 / 全宗隔离漏判
- 项目历史高频返工点（必查）：
  - `DocumentPoolServiceImpl.resolveVoucher` 禁止新增回退路径（先写契约再补测试，违反即 P0）
  - Redis 缓存逻辑修复后未清旧缓存（dashboardStats / groupedFonds / fondsScope）
  - mock/demo 数据 fonds 用错（必须 `BR-DEMO` 且 `arc_original_voucher` / `arc_file_content` / `acc_archive` 三表同步）
  - PDF 链路历史约束（SM3 文件校验、`PdfTaskStatus` 枚举、下载接口 fonds 隔离、格式转换审计日志）
  - 改动类字段长度/类型后，DDL 与 Entity/MyBatis 映射不一致

逐条去证明"真的没有"，并给出行号证据。

---

## 补充阶段：部署与回滚风险评估（上线前必查）

原框架九阶段全是代码视角，但对已上线系统，部署与回滚才是最后防线：

- **回滚可行性**：Flyway 迁移是否可回滚（有无 DROP/破坏性 DDL）；"回滚旧代码 + 新 schema"组合是否兼容
- **部署顺序**：前后端是否有顺序依赖（新前端调旧后端接口是否存在；旧前端调新后端响应是否兼容）
- **配置变更清单**：新增/修改的环境变量、Nginx、docker-compose、密钥是否已列清单并同步部署文档/客户档案（漏配 env 是上线事故高发区）
- **静态资源路径**：前端产物是否走版本化 `system-assets/[releaseId]/` 路径（demo 环境必须 `build-demo-release.sh`，禁止直接 `npm run build` 部署）
- **客户环境差异**：mjy/fsk 等现场版本基线、Flyway checksum 是否与本 PR 兼容

每项给出 PASS/FAIL + 证据；回滚不可行时必须给出前置防护方案（先兼容后切换、特性开关等）。

---

## 第八阶段：证据驱动（Evidence Driven Review）

任何"没问题"都必须提供证据。

**禁止写法：**

```
没有空指针。
```

**必须写法：**

```
PASS — 空值检查
证据：
- DocumentPoolServiceImpl.java:134 Objects.requireNonNull(batchId)
- DocumentPoolServiceImpl.java:288 Optional.ofNullable(...).orElseThrow(...)
所有入口均进行 null 检查。
```

每一个 PASS 都必须有对应证据（文件:行号 + 代码片段）。没有证据的检查项一律按 FAIL 处理。

---

## 第九阶段：最终裁决

最后不能写"看起来没问题"，必须二选一：

```
PASS — 可以上线
```

或

```
FAIL — 禁止上线
```

问题分级：

- **P0**：必须修复，否则禁止上线
- **P1**：建议上线前修复
- **P2**：可后续优化，不影响当前发布

---

## 输出模板

```markdown
## Production Risk Review 结论

### 第一阶段：改动理解
| 项目 | 内容 |
| --- | --- |
| 修改目的 | ... |
| 修改模块 | ... |
| ...（9 项全列） | ... |

调用链：<画完整链路>

### 第二阶段：影响分析
<Dependency Expansion 结果，列出全部受影响方>

### 第三阶段：Bug 推演
<至少 3 条故障推演链，每条到根因>

### 第四阶段：分类检查
| 检查项 | 结论 | 证据 |
| --- | --- | --- |
| 空值 | PASS/FAIL | 文件:行号 |
| ... | ... | ... |

### 第五阶段：业务回归
<逐业务链验证结果>

### 第六阶段：极端场景
<逐场景推演 + 证据>

### 第七阶段：隐藏 Bug 排查
<逐条证伪 + 行号>

### 部署与回滚评估
<回滚可行性 / 部署顺序 / 配置清单 / 客户环境兼容性，逐项证据>

### 发现的问题
- [P0] 文件:行号 — 问题描述 — 修复建议
- [P1] ...
- [P2] ...

### 最终裁决
✅ PASS — 可以上线 / ❌ FAIL — 禁止上线
<一句话理由>

### 上线后验证清单（PASS 时必填）
- [ ] health 接口 200
- [ ] Flyway 迁移全部成功（核对版本数）
- [ ] 登录页 302 / 登录流程冒烟
- [ ] 本次改动核心路径手工冒烟
- [ ] 涉及的 Redis 缓存已清理（如适用）

### 未审计声明
<如有跳过或降级执行的阶段，显式列出并说明残余风险；无则写"全部阶段已执行">
```

---

## 执行纪律

- 全部阶段**顺序执行**，禁止跳过；时间紧也至少要完成第一、二、四、八、九阶段，且**跳过的阶段必须在报告"未审计声明"中显式披露残余风险**
- 第二阶段的依赖扩展与第四阶段的分类检查，可用多个 search agent 并行取证，但证据汇总与裁决必须由主审计完成
- 所有 grep/读代码必须真实执行，禁止凭印象写"未发现"
- 涉及 Flyway、权限、全宗隔离、归档 ID 类型的改动，自动升级为最高警惕级别
- 裁决为 PASS 时必须附"上线后验证清单"；裁决为 FAIL 时，明确列出阻断上线的 P0 项及修复路径
