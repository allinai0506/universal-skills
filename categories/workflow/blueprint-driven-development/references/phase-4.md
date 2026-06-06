# Phase 4 — 验证

> **最关键的验证阶段。每个角色都要有 Playwright 截图作为证据。**

---

## 前置条件

检查点 phase=4 且编译/构建通过

---

## 步骤 1：启动服务

```bash
export XIYU_DEV_CONFIRMED=1
WORKTREE=$(git rev-parse --show-toplevel)
source "$WORKTREE/scripts/dev-env.sh"
```

参考：`references/service-startup.md`

---

## 步骤 2：获取 Token

```bash
bash .claude/skills/blueprint-driven-development/scripts/get-tokens.sh --verbose
```

如果失败，参考 `references/troubleshooting.md`。

读取各角色 token：

```bash
cat /tmp/blueprint-tokens.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d)"
```

---

## 步骤 3：Playwright 页面验证

使用 `scripts/verify-page.js` 辅助函数在 Playwright 中验证：

**必做验证项**（每个角色都要跑）：

1. ✅ 登录后页面正常加载
2. ✅ 能看到标讯列表（所有角色都能看）
3. ✅ 创建按钮只出现在有权限的角色（对照 `references/role-permissions.md`）
4. ✅ 无权限的按钮/操作确实不出现
5. ✅ 状态流转：提交 → 审核通过/拒绝

### 使用 verify-page.js 辅助函数

```javascript
const v = /* 粘贴 scripts/verify-page.js 内容 */;
const page = /* Playwright page */;

// 登录
await v.loginWithToken(page, 'http://127.0.0.1:3000', token);

// 导航
await page.goto('http://127.0.0.1:3000/bidding');
await v.waitForPageReady(page);

// 批量验证权限
const checks = [
  { type: 'button', expected: '创建标讯' },
  { type: 'no-button', expected: '删除' },
];
const results = await v.batchVerify(page, checks);

// 截图
// 使用 browser_take_screenshot 工具
```

完整参考：`references/playwright-verification.md`

---

## 步骤 4：交叉验证

对照 Phase 2 gap-analysis.md 的每一行：
- ✅ gap-analysis 说已实现的 → 验证真的实现了
- ✅ gap-analysis 说未实现的 → 验证真的修复了

---

## 步骤 5：输出验证报告

写入 `verify-roles.md`：

```markdown
# 角色验证报告 - §4.2.1

**验证时间**: 2026-06-06
**Token 来源**: /tmp/blueprint-tokens.json

## bid_admin
✅ 创建标讯按钮可见
✅ 编辑按钮可见
✅ 删除按钮可见

截图：bid-admin-4.2.1.png

## sales
✅ 创建标讯按钮可见
✅ 编辑按钮不可见（无权限）
```

---

## 完成后

```bash
WORKTREE=$(git rev-parse --show-toplevel)
echo '{"section":"4.2.1","phase":5,"phases_done":[1,2,3,4],"worktree":"'"$WORKTREE"'"}' > "$WORKTREE/.blueprint-checkpoint.json"
```
