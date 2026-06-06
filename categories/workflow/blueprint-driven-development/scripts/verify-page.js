/**
 * Blueprint Verification Helpers v2
 *
 * Inject via browser_run_code_unsafe. All functions return structured data
 * the agent can analyze to verify blueprint compliance.
 *
 * Usage:
 *   const v = <paste BlueprintVerify source here>;
 *   const page = /* Playwright page object *\/;
 *   return await v.getVisibleButtons(page);
 */

const BlueprintVerify = {

  // ── Login ────────────────────────────────────────────────────────────────

  /**
   * Login by injecting token into localStorage and reloading.
   * Handles Vue Router's token validation on mount.
   */
  async loginWithToken(page, url, token) {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    await page.evaluate((t) => {
      localStorage.clear();
      localStorage.setItem('token', t);
    }, token);
    await page.goto(url, { waitUntil: 'networkidle' });
    await this.waitForPageReady(page);
  },

  // ── Page readiness ───────────────────────────────────────────────────────

  async waitForPageReady(page, timeoutMs = 6000) {
    await page.waitForLoadState('networkidle', { timeout: timeoutMs }).catch(() => {});
    await page.waitForTimeout(1200);
  },

  // ── Buttons ─────────────────────────────────────────────────────────────

  async getVisibleButtons(page) {
    const buttons = await page.locator('button, [role="button"], .el-button').all();
    const texts = [];
    for (const btn of buttons) {
      if (await btn.isVisible()) {
        const t = (await btn.textContent() || '').trim().replace(/\s+/g, ' ');
        if (t) texts.push(t);
      }
    }
    return [...new Set(texts)].sort();
  },

  async hasButton(page, text) {
    const btn = page.locator(
      `button:has-text("${text}"), [role="button"]:has-text("${text}"), .el-button:has-text("${text}")`
    ).first();
    return btn.isVisible().catch(() => false);
  },

  async waitForButton(page, text, timeoutMs = 5000) {
    const btn = page.locator(
      `button:has-text("${text}"), [role="button"]:has-text("${text}"), .el-button:has-text("${text}")`
    ).first();
    await btn.waitFor({ state: 'visible', timeout: timeoutMs }).catch(() => null);
    return btn.isVisible().catch(() => false);
  },

  // ── Tables ──────────────────────────────────────────────────────────────

  async getTableHeaders(page, tableSelector = '.el-table, table') {
    const table = page.locator(tableSelector).first();
    if (!(await table.isVisible().catch(() => false))) return [];
    const headers = await table.locator('th, .el-table__header th').all();
    const texts = [];
    for (const h of headers) {
      const t = (await h.textContent() || '').trim();
      if (t) texts.push(t);
    }
    return texts;
  },

  async getTableRowCount(page, tableSelector = '.el-table, table') {
    const table = page.locator(tableSelector).first();
    if (!(await table.isVisible().catch(() => false))) return 0;
    return await table.locator('tbody tr, .el-table__body tr').count();
  },

  async getTableCell(page, row, col, tableSelector = '.el-table, table') {
    const table = page.locator(tableSelector).first();
    if (!(await table.isVisible().catch(() => false))) return null;
    const cell = table.locator('tbody tr, .el-table__body tr').nth(row)
      .locator('td').nth(col);
    if (!(await cell.isVisible().catch(() => false))) return null;
    return (await cell.textContent() || '').trim();
  },

  // ── Form fields ─────────────────────────────────────────────────────────

  async getFormLabels(page, formSelector = 'form, .el-form') {
    const form = page.locator(formSelector).first();
    if (!(await form.isVisible().catch(() => false))) return [];
    const labels = await form.locator('label, .el-form-item__label').all();
    const texts = [];
    for (const lbl of labels) {
      const t = (await lbl.textContent() || '').trim();
      if (t) texts.push(t);
    }
    return texts;
  },

  async fillFormField(page, labelOrPlaceholder, value) {
    // Try label association first
    const input = page.locator(
      `label:has-text("${labelOrPlaceholder}") + * input,` +
      `label:has-text("${labelOrPlaceholder}") ~ * input,` +
      `[placeholder="${labelOrPlaceholder}"],` +
      `.el-input__inner[placeholder="${labelOrPlaceholder}"]`
    ).first();
    if (await input.isVisible().catch(() => false)) {
      await input.clear();
      await input.fill(value);
      return true;
    }
    return false;
  },

  async getInputValue(page, labelOrName) {
    const input = page.locator(
      `label:has-text("${labelOrName}") + * input,` +
      `label:has-text("${labelOrName}") ~ * input,` +
      `[name="${labelOrName}"],` +
      `.el-input:has(input[name="${labelOrName}"]) .el-input__inner`
    ).first();
    if (!(await input.isVisible().catch(() => false))) return null;
    return (await input.inputValue()) || null;
  },

  // ── Navigation & tabs ──────────────────────────────────────────────────

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

  async clickTab(page, tabText) {
    const tab = page.locator(
      `.el-tabs__item:has-text("${tabText}"), [role="tab"]:has-text("${tabText}")`
    ).first();
    if (await tab.isVisible().catch(() => false)) {
      await tab.click();
      await this.waitForPageReady(page);
      return true;
    }
    return false;
  },

  // ── Text & element visibility ────────────────────────────────────────────

  async isElementVisible(page, text) {
    const el = page.locator(`text="${text}"`).first();
    return el.isVisible().catch(() => false);
  },

  async getElementTexts(page, selector) {
    const els = await page.locator(selector).all();
    const texts = [];
    for (const el of els) {
      if (await el.isVisible().catch(() => false)) {
        const t = (await el.textContent() || '').trim();
        if (t) texts.push(t);
      }
    }
    return texts;
  },

  // ── Batch verification ───────────────────────────────────────────────────

  /**
   * Verify multiple conditions at once.
   * checks: [{ type: 'button'|'no-button'|'text'|'no-text'|'tab', expected: string }, ...]
   */
  async batchVerify(page, checks) {
    const results = [];
    for (const c of checks) {
      let passed = false;
      try {
        switch (c.type) {
          case 'button':
            passed = await this.hasButton(page, c.expected);
            break;
          case 'no-button':
            passed = !(await this.hasButton(page, c.expected));
            break;
          case 'text':
            passed = await this.isElementVisible(page, c.expected);
            break;
          case 'no-text':
            passed = !(await this.isElementVisible(page, c.expected));
            break;
          case 'tab':
            passed = (await this.getTabs(page)).includes(c.expected);
            break;
          case 'no-tab':
            passed = !(await this.getTabs(page)).includes(c.expected);
            break;
        }
      } catch (_) {
        passed = false;
      }
      results.push({ check: c.expected, type: c.type, passed });
    }
    return results;
  },

  // ── Screenshot helper ───────────────────────────────────────────────────

  async screenshotNamed(page, name) {
    // The actual screenshot is taken by the browser_take_screenshot tool.
    // This helper just returns the suggested filename for documentation.
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    return `${name}-${ts}.png`;
  },

  // ── Page metadata ───────────────────────────────────────────────────────

  getCurrentUrl(page) {
    return page.url();
  },

  getPageTitle(page) {
    return page.title();
  },

  async getBreadcrumb(page) {
    const els = await page.locator('.el-breadcrumb__item, [class*="breadcrumb"] span, nav [class*="breadcrumb"] span').all();
    const crumbs = [];
    for (const el of els) {
      if (await el.isVisible().catch(() => false)) {
        const t = (await el.textContent() || '').trim();
        if (t) crumbs.push(t);
      }
    }
    return crumbs;
  },

  // ── Role verification report ───────────────────────────────────────────

  /**
   * Generate a structured role verification report.
   * Verifies each role's visible buttons against an expected matrix.
   *
   * @param {object} page - Playwright page
   * @param {string} url - Target URL
   * @param {object} tokenMap - { role: token } from /tmp/blueprint-tokens.json
   * @param {object[]} permissionMatrix - [{ role, shouldSee: string[], shouldNotSee: string[] }]
   */
  async verifyRoles(page, url, tokenMap, permissionMatrix) {
    const report = {};
    for (const entry of permissionMatrix) {
      const { role, shouldSee = [], shouldNotSee = [] } = entry;
      const token = tokenMap[role];
      if (!token) {
        report[role] = { error: 'No token available' };
        continue;
      }

      await this.loginWithToken(page, url, token);
      const visible = await this.getVisibleButtons(page);

      const seeResults = shouldSee.map(btn => ({
        button: btn,
        passed: visible.includes(btn),
      }));
      const noSeeResults = shouldNotSee.map(btn => ({
        button: btn,
        passed: !visible.includes(btn),
      }));

      report[role] = {
        buttons: visible,
        shouldSee: seeResults,
        shouldNotSee: noSeeResults,
        allPassed: [...seeResults, ...noSeeResults].every(r => r.passed),
      };
    }
    return report;
  },
};
