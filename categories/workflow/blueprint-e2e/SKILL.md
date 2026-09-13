---
name: blueprint-e2e
description: >
  针对飞书产品蓝图的每一个小节（小节粒度，如 4.2.1、4.3.2），独立编写和执行 Playwright E2E 测试，
  验证功能实现是否符合蓝图需求。测试即文档——E2E 测试是对蓝图需求的机器可执行描述。
  触发场景：用户提到"E2E 测试蓝图书"、"做蓝图的 E2E"、"测试某小节"、"e2e 覆盖"、"推进 E2E"、
  "验证蓝图测试覆盖"、"blueprint E2E"、"蓝图书 e2e"、"补充测试覆盖"、"测试即文档"。
  与 blueprint-driven-development 的区别：后者负责"实现"功能，本技能负责"验证"实现是否符合蓝图。
  核心原则：每个蓝图小节必须有对应 E2E spec，不存在 = 未完成。
  含测试覆盖缺口检测、Playwright 脚本自动生成辅助、CI 门禁绑定。
---

# 蓝图书 E2E 测试工作流

> **本技能与 `blueprint-driven-development` 配套使用。**
> - `blueprint-driven-development` 负责**实现**功能（做对）
> - `blueprint-e2e` 负责**验证**实现是否符合蓝图（证明做对了）
> - 测试即文档：E2E 测试是对蓝图需求的行为描述

> **测试即文档原则**：E2E 测试是蓝图需求的行为文档。每个 `test()` 是对蓝图某一功能点/权限矩阵/状态流转的机器可执行描述。

---

## 快速命令

```bash
# 检测当前蓝图小节的 E2E 覆盖状态（返回已覆盖 / 覆盖不完整 / 未覆盖）
node .claude/skills/blueprint-e2e/scripts/check-coverage.mjs --section 4.3.2

# 为蓝图小节生成 E2E 测试骨架
node .claude/skills/blueprint-e2e/scripts/generate-skeleton.mjs --section 4.3.2 --module brand-auth

# 运行指定蓝图小节的 E2E 测试
node .claude/skills/blueprint-e2e/scripts/run-section.mjs --section 4.3.2

# 自动检测端口和数据库
source scripts/dev-env.sh
```

---

## 测试即文档原则

E2E 测试是蓝图需求的行为文档。每个 `test()` 是对蓝图某一功能点/权限矩阵/状态流转的机器可执行描述。

| 蓝图内容 | E2E 表达 |
|---------|---------|
| 功能点 | 一个 `test()` |
| 权限矩阵 | 每个角色一个 `test()` |
| 状态流转 | 每个状态转换一个 `test()` |
| 边界情况 | `test()` 带 `test.skip()` 或 `test.fixme()` |
| 蓝图截图要求 | 对应 `expect(page.screenshot()).toMatchSnapshot()` |

---

## 工作流总览

```
读蓝图 → 探现状 → 析覆盖缺口 → 写/补 E2E → 运行验证 → 提交
```

```
blueprint-driven-development          blueprint-e2e
┌──────────────────────┐         ┌──────────────────────┐
│  1. 读蓝图           │         │  1. 读蓝图           │
│  2. 探代码           │         │  2. 探现状（现有spec）│
│  3. 析差距           │         │  3. 析覆盖缺口       │
│  4. 定方案           │         │  4. 写/补 E2E        │
│  5. 写代码           │         │  5. 运行验证         │
│  6. 启动服务         │         │  6. 提交             │
│  7. 真实验证         │◄────────│  ← 验证结果反馈     │
│  8. 修 Bug           │         │                      │
│  9. 门禁+测试        │         │                      │
│  10. 提交            │         │                      │
└──────────────────────┘         └──────────────────────┘
```

---

## 第 1 步：读蓝图

用 `lark-doc` 读取飞书产品蓝图的指定小节，提取：

- **功能点列表**：每个功能对应一个测试
- **权限矩阵**：哪些角色可以/不可以做什么
- **状态流转定义**：状态机转换规则
- **表单字段要求**：必填、可选、格式校验
- **边界情况和错误提示要求**

```bash
lark-cli docs +fetch --api-version v2 \
  --doc "https://my.feishu.cn/docx/FgLAdRmFho4QhwxncgAcfxKJn0d" \
  --scope outline --max-depth 5

lark-cli docs +fetch --api-version v2 \
  --doc "https://my.feishu.cn/docx/FgLAdRmFho4QhwxncgAcfxKJn0d" \
  --scope section --start-block-id <章节的block-id> \
  --detail full --format pretty
```

将读取结果记录到 `e2e-coverage/<section>.md`：

```markdown
# E2E 覆盖分析 - 小节 [4.3.2]

## 蓝图功能点
- [ ] 原厂授权列表查看
- [ ] 新增原厂授权
- [ ] 编辑原厂授权
- [ ] 作废原厂授权
- [ ] 详情查看

## 权限矩阵
| 角色 | 查看列表 | 新增 | 编辑 | 作废 |
|------|---------|------|------|------|
| bid_admin | ✅ 全量 | ✅ | ✅ | ✅ |
| bid_lead | ✅ 全量 | ✅ | ✅ | ✅ |
| sales | — | — | — | — |
| bid_specialist | ✅ 全量 | — | — | — |

## 状态流转
NORMAL → REVOKED（作废后不可编辑）

## 需测试的边界情况
- 空列表状态
- 作废原因 <10 字按钮禁用
- 作废原因 ≥10 字可确认
- 作废后状态标签显示
- 作废后编辑/作废按钮隐藏
```

---

## 第 2 步：探现状

### 2.1 查找现有 E2E 测试

```bash
# 搜索与该小节相关的现有 spec 文件
grep -rl "4.3.2\|brand-auth" e2e/ --include="*.spec.js" || echo "未找到"

# 列出所有 spec 文件
ls e2e/*.spec.js | sort
```

### 2.2 运行覆盖检测脚本

```bash
node .claude/skills/blueprint-e2e/scripts/check-coverage.mjs --section 4.3.2 --verbose
```

输出示例：
```
🔍 覆盖率检测：小节 4.3.2
──────────────────────────────────────────────────────────────
✅ brand-auth-manufacturer-flow.spec.js
   测试总数: 11  (通过: 8 | skip: 2 | fixme: 1)

📊 分类覆盖分析
   ✅ 正向流程
   ✅ 权限验证
   ⚠️  状态流转（仅 1/4 测试）
   ❌ 边界情况（缺失空列表测试）

📈 总覆盖度: 60% (3/5 类)
👤 角色权限覆盖
   ✅ bid_admin
   ✅ bid_lead
   ✅ sales
   ✅ bid_specialist
   ⚠️  staff（缺少仅查看验证）
```

---

## 第 3 步：析覆盖缺口

基于第 1 步的蓝图分析 + 第 2 步的探现状结果，生成缺口表：

```markdown
# E2E 缺口分析 - 小节 [4.3.2]

## 缺口表

| 缺口 ID | 蓝图功能点 | 测试文件 | 现状 | 修复方式 |
|---------|---------|---------|------|---------|
| G-01 | 编辑授权流程 | `brand-auth-manufacturer-flow.spec.js` | 缺失 | 新增 test() |
| G-02 | 作废授权完整流程 | `brand-auth-manufacturer-flow.spec.js` | 部分覆盖 | 补充作废原因字数校验 |
| G-03 | 详情页查看 | `brand-auth-manufacturer-flow.spec.js` | 缺失 | 新增 test() |
| G-04 | 附件上传流程 | `brand-auth-manufacturer-flow.spec.js` | 缺失 | 新增 test() |
| G-05 | 分页导航 | `brand-auth-manufacturer-flow.spec.js` | 缺失 | 新增 test() |
| G-06 | staff 角色仅查看 | `brand-auth-manufacturer-flow.spec.js` | 缺失 | 新增 test() |
| G-07 | 作废后状态标签 | `brand-auth-manufacturer-flow.spec.js` | 缺失 | 新增 test() |
| G-08 | 作废后不可编辑 | `brand-auth-manufacturer-flow.spec.js` | 缺失 | 新增 test() |
| G-09 | 空列表状态 | `brand-auth-manufacturer-flow.spec.js` | 缺失 | 新增 test() |
| G-10 | 导出功能"即将上线" | `brand-auth-manufacturer-flow.spec.js` | 缺失 | 新增 test() |

## 覆盖率目标
- 当前: 26% (11/42 测试用例)
- 目标: 100% (42/42 测试用例)
- 缺口: 31 个测试用例
```

---

## 第 4 步：写 / 补 E2E

### 4.1 命名规范

```
e2e/<模块>-<功能>-<场景>.spec.js
```

示例：
- `e2e/brand-auth-manufacturer-flow.spec.js` — 品牌原厂授权全流程
- `e2e/brand-auth-agent-flow.spec.js` — 品牌代理商授权
- `e2e/tender-list-permission.spec.js` — 标讯列表权限验证
- `e2e/tender-state-flow.spec.js` — 标讯状态流转

### 4.2 标准测试结构

每个 `*.spec.js` 必须包含以下 `test.describe` 分组：

1. **【正向流程】** — 主功能流程（新增/编辑/作废/详情）
2. **【权限验证】** — 角色视角检查（每个角色可见/可操作什么）
3. **【表单校验】** — 字段校验（必填、格式、唯一性）
4. **【状态流转】** — 状态机验证
5. **【边界情况】** — 异常与错误处理

### 4.3 测试模板

详见 `references/test-template.md`

### 4.4 辅助函数

使用 `e2e/auth-helpers.js` 中的 `ensureApiSession` + `injectSession`：

```javascript
import { ensureApiSession, injectSession } from './auth-helpers.js'
```

使用骨架生成器生成测试：

```bash
node .claude/skills/blueprint-e2e/scripts/generate-skeleton.mjs \
  --section 4.3.2 \
  --module brand-auth \
  --out e2e/brand-auth-manufacturer-flow.spec.js
```

### 4.5 注意事项

- **每个测试使用独立用户名**（带时间戳 suffix）避免会话冲突
- **重试策略**：`playwright.config.js` 中 `retries: CI ? 1 : 0`
- **截图**：`playwright.config.js` 配置 `screenshot: 'only-on-failure'`
- **依赖外部 AI Provider 的测试**：用 `test.skip()` 标记并注明原因
- **未实现功能**：用 `test.fixme()` 标记
- **路由守卫拦截**：权限不足角色直接访问 URL 时应被拦截
- **test.skip() 不等于不写**：skip 的测试要写完整逻辑，只是暂时跳过

### 4.6 权限验证标准模式

```javascript
// ✅ 正确：用 HaveCount(0) 检查按钮不存在
const btn = page.getByRole('button', { name: '删除' })
await expect(btn).toHaveCount(0)

// ❌ 错误：用 toBeHidden() 可能误报
await expect(btn).not.toBeVisible()
```

---

## 第 5 步：运行验证

### 5.1 确保服务已启动

```bash
export XIYU_DEV_CONFIRMED=1
source scripts/dev-env.sh

# 检查后端健康
curl -s http://127.0.0.1:${BACKEND_PORT}/actuator/health

# 检查前端可访问
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:${FRONTEND_PORT}
```

### 5.2 运行测试

```bash
# 运行指定 spec
PLAYWRIGHT_BASE_URL=http://127.0.0.1:${FRONTEND_PORT} \
PLAYWRIGHT_API_BASE_URL=http://127.0.0.1:${BACKEND_PORT} \
npx playwright test e2e/brand-auth-manufacturer-flow.spec.js \
  --config playwright.config.js

# 运行蓝图小节相关所有测试
node .claude/skills/blueprint-e2e/scripts/run-section.mjs --section 4.3.2

# 全量 E2E（仅 CI）
npm run test:e2e
```

### 5.3 解读测试结果

| 结果 | 含义 | 行动 |
|------|------|------|
| `passed` | 测试通过（实现符合蓝图） | ✅ 完成 |
| `failed` | 功能未实现或行为不对齐 | 修复代码后重跑 |
| `skipped` | 用 `test.skip()` 标记，功能未实现 | 后续实现后移除 skip |
| `fixme` | 用 `test.fixme()` 标记，待修复 | 跟踪记录 |
| `timed-out` | 页面加载超时 | 检查网络或后端响应 |

---

## 第 6 步：CI 门禁绑定

每个蓝图小节的 E2E 测试结果与门禁挂钩：

### E2E 覆盖率门禁（Gate E1）

如果蓝图小节有对应 `e2e-coverage/<section>.md` 但相关 `.spec.js` 不存在 → **commit 被拦截**：

```bash
node .claude/skills/blueprint-e2e/scripts/check-coverage.mjs --section 4.3.2 --strict
```

### 测试通过门禁（Gate E2）

如果存在 `.spec.js` 但有 `failed` 测试 → **不允许合入 main**：

```bash
# 在 PR CI 中运行
PLAYWRIGHT_BASE_URL=http://127.0.0.1:1314 \
PLAYWRIGHT_API_BASE_URL=http://127.0.0.1:18080 \
npx playwright test e2e/ --config playwright.config.js
```

### 覆盖率趋势门禁（Gate E3）

每次 PR 的覆盖率不得低于上一版本的 90%：

```bash
node .claude/skills/blueprint-e2e/scripts/check-coverage.mjs \
  --section 4.3.2 --trend --baseline iteration-1
```

---

## 第 7 步：提交

```bash
git add e2e/ e2e-coverage/
git commit -m "test(e2e): 小节 4.3.2 — 补充 E2E 测试覆盖

- 新增 brand-auth-manufacturer-flow.spec.js（正向流程 + 权限验证）
- 补充作废流程测试（作废原因字数校验）
- 补充边界情况测试（空列表、导出即将上线）
- 覆盖率: 11 → 42 测试用例

[skip e2e-scope]"
git push origin <branch-name>
```

> `[skip e2e-scope]` 用于纯测试更新的 PR，标记不涉及功能实现。

---

## 常见问题

### Q: 功能未实现，但我想先写测试
A: 用 `test.skip()` 或 `test.fixme()` 标记，测试骨架会进入版本控制，CI 会跟踪进度。

### Q: 多个蓝图小节共用同一个页面，测试文件怎么组织
A: 按页面组织 spec 文件，在 describe 标题中标注涉及的蓝图小节。例如 `e2e/tender-form.spec.js` 覆盖 4.2.1 + 4.2.2。

### Q: 如何让 CI 只跑受影响的 spec
A: 使用 `node .claude/skills/blueprint-e2e/scripts/run-section.mjs --section 4.3.2`。

### Q: 测试偶发失败（flaky）
A: 检查后端日志；增加 `await page.waitForTimeout(500)` 或用 `waitForResponse` 代替固定等待。

### Q: 蓝图和实现不一致，以哪个为准
A: 以蓝图为准。如果发现实现与蓝图不符，应在 gap table 中记录，并在 PR 描述中说明差异。

---

## 参考文件

- 测试模板：`.claude/skills/blueprint-e2e/references/test-template.md`
- 角色权限矩阵：`.claude/skills/blueprint-e2e/references/role-permissions.md`
- Playwright 配置：`playwright.config.js`
- 认证辅助：`e2e/auth-helpers.js`
- 完整参考指南：`.claude/skills/blueprint-e2e/references/blueprint-e2e-guide.md`
