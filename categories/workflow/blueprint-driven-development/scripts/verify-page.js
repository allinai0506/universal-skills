// Blueprint Verification Helpers — inject via browser_run_code_unsafe
//
// These functions are designed to run inside the browser via Playwright's
// browser_run_code_unsafe MCP tool. Each returns structured data the agent
// can analyze to verify blueprint compliance.
//
// Usage example in browser_run_code_unsafe:
//   const v = <paste BlueprintVerify source here>;
//   return await v.getVisibleButtons();

const BlueprintVerify = {

  // Get all visible button texts (de-duplicated, sorted)
  async getVisibleButtons(page) {
    const buttons = await page.locator('button, [role="button"], .el-button').all();
    const texts = [];
    for (const btn of buttons) {
      if (await btn.isVisible()) {
        const t = (await btn.textContent() || '').trim();
        if (t) texts.push(t);
      }
    }
    return [...new Set(texts)].sort();
  },

  // Check if a button with specific text is visible
  async hasButton(page, text) {
    const btn = page.locator(`button:has-text("${text}"), [role="button"]:has-text("${text}")`).first();
    return btn.isVisible();
  },

  // Get table/el-table column headers
  async getTableHeaders(page, tableSelector = '.el-table, table') {
    const table = page.locator(tableSelector).first();
    if (!(await table.isVisible())) return [];
    const headers = await table.locator('th, thead th, .el-table__header th').all();
    const texts = [];
    for (const h of headers) {
      const t = (await h.textContent() || '').trim();
      if (t) texts.push(t);
    }
    return texts;
  },

  // Get table row count
  async getTableRowCount(page, tableSelector = '.el-table, table') {
    const table = page.locator(tableSelector).first();
    if (!(await table.isVisible())) return 0;
    return await table.locator('tbody tr, .el-table__body tr').count();
  },

  // Check element by text content exists and is visible
  async isElementVisible(page, text) {
    const el = page.locator(`text="${text}"`).first();
    return el.isVisible();
  },

  // Get current page URL
  getCurrentUrl(page) {
    return page.url();
  },

  // Wait for page to load (network idle)
  async waitForPageReady(page, timeoutMs = 5000) {
    await page.waitForLoadState('networkidle', { timeout: timeoutMs }).catch(() => {});
    await page.waitForTimeout(1000); // extra settle time for Vue
  },

  // Verify multiple conditions at once (batch check)
  async batchVerify(page, checks) {
    // checks: [ { type: 'button'|'text'|'header', expected: string }, ... ]
    const results = [];
    for (const c of checks) {
      let passed = false;
      switch (c.type) {
        case 'button':
          passed = await BlueprintVerify.hasButton(page, c.expected);
          break;
        case 'text':
          passed = await BlueprintVerify.isElementVisible(page, c.expected);
          break;
        case 'no-button':
          passed = !(await BlueprintVerify.hasButton(page, c.expected));
          break;
        case 'no-text':
          passed = !(await BlueprintVerify.isElementVisible(page, c.expected));
          break;
      }
      results.push({ check: c.expected, type: c.type, passed });
    }
    return results;
  },

  // Get all tab/step texts (for workflow state verification)
  async getTabs(page, tabSelector = '.el-tabs__item, [role="tab"]') {
    const tabs = await page.locator(tabSelector).all();
    const texts = [];
    for (const tab of tabs) {
      if (await tab.isVisible()) {
        const t = (await tab.textContent() || '').trim();
        if (t) texts.push(t);
      }
    }
    return texts;
  },

  // Inject token into localStorage and navigate
  async loginWithToken(page, url, token) {
    await page.goto(url);
    await page.waitForTimeout(1500);
    await page.evaluate((t) => {
      localStorage.clear();
      localStorage.setItem('token', t);
    }, token);
    await page.goto(url);
    await BlueprintVerify.waitForPageReady(page);
  }
};
