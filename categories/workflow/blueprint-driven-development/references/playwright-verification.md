# Playwright 验证代码参考

## 使用 verify-page.js 辅助函数

```javascript
// 在 browser_run_code_unsafe 中使用
const v = <从 verify-page.js 粘贴内容>;
const page = /* Playwright 的 page 对象 */;

// 1. 登录
await v.loginWithToken(page, 'http://127.0.0.1:<FRONTEND_PORT>', '<token>');

// 2. 导航到目标页面
await page.goto('http://127.0.0.1:<FRONTEND_PORT>/bidding');
await v.waitForPageReady(page);

// 3. 获取可见按钮
const buttons = await v.getVisibleButtons(page);

// 4. 批量验证权限
const checks = [
  { type: 'button', expected: '创建标讯' },
  { type: 'button', expected: '编辑' },
  { type: 'no-button', expected: '删除' },
];
const results = await v.batchVerify(page, checks);

// 5. 截图
// 用 browser_take_screenshot 工具

return { buttons, permissionResults: results };
```

## 脚本路径

- `scripts/get-tokens.sh` — 获取各角色 token
- `scripts/verify-page.js` — Playwright 辅助函数
- `references/role-permissions.md` — 角色权限矩阵参考
