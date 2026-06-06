# 根因猎手调试报告模板

## 元信息

| 项目 | 内容 |
|------|------|
| **报告编号** | RCH-YYYY-MM-DD-001 |
| **Bug ID** | [链接或编号] |
| **报告时间** | [时间戳] |
| **调试人员** | [AI Agent] |
| **严重性** | [CRITICAL / MAJOR / MINOR] |
| **Bug 类型** | [缓存失效 / 乐观锁竞态 / 架构违规 / ...] |

---

## 1. 现场还原（The Crime Scene）

### 症状素描

> [一句话精准描述 Bug - 不仅是报错，而是业务上的"失能"]

### 边界划定

> [什么情况下它是**绝对不会**发生的？排除干扰项]

### 技术栈推断

> 根据栈帧包名推断：
> - `jakarta.*` / `org.springframework.*` → Java/Spring Boot
> - `com.xiyu.bid.*` → 西域投标平台后端
> - `wx.*` → 微信小程序
> - `react` / `@mui` → React 前端

### 思维沙箱

> [需要获取 X 信息] 或 [信息充足，跳过]

---

## 2. 剥洋葱：逆向调用链

### Layer 3 (IO/数据层)

| 检查项 | 预期 | 实际 | 偏差 |
|--------|------|------|------|
| [数据库查询] | [...] | [...] | [...] |
| [网络请求] | [...] | [...] | [...] |
| [文件读写] | [...] | [...] | [...] |

### Layer 2 (核心逻辑层)

| 状态 | 值 | 位置 |
|------|-----|------|
| 输入状态 | [变量=值] | [文件:行] |
| 中间状态 | [变量=值] | [文件:行] |
| 输出状态 | [变量=值] | [文件:行] |

**分叉点**：`[文件名:行号]` - [描述]

### Layer 1 (入口/参数层)

| 参数 | 预期类型/范围 | 实际值 | 来源 |
|------|--------------|--------|------|
| [参数名] | [...] | [...] | [...] |

---

## 3. 零号病人定位

### 第一行错误

```file
path/to/file.ts:42
return result; // result 在这里是 undefined
```

### 必然性解释

```
1. 调用 A() 返回 null（因为数据库无匹配记录）
2. B() 将 null 存入 cache
3. C() 从 cache 读取 null
4. D() 对 null 调用 .map() → TypeError

必然崩溃：因为 D 假设输入永远是数组，但 B 允许 null 进入 cache
```

### 状态变迁图

```
      DB Query
         ↓
    (no record)
         ↓
      A() → null
         ↓
    [cache写入]
         ↓
      B() 允许 null
         ↓
    C() 读取 null
         ↓
      D().map() ← 💥 崩溃
```

---

## 4. Bug 类型分类

| 现象特征 | Bug 类型 | 命中域 |
|----------|---------|--------|
| [特征] | [类型] | [域] |

---

## 5. 验证与修复

### 最小验证

```bash
# 在 file.ts:42 前添加
$ redis-cli GET cache:tender:123
(nil)  ← 预期：有值；实际：nil → Cache Miss 确认
```

### 手术式修复

```diff
--- a/path/to/file.ts
+++ b/path/to/file.ts
@@ -39,7 +39,7 @@ function processItems(items) {
-  const result = cache.get(key);
+  const result = cache.get(key) ?? DEFAULT_EMPTY_LIST;
   return result.map(transform);
```

### 防复发锁

```javascript
// 添加运行时断言
assert(Array.isArray(result), `cache invariant violated: ${key} must be array`);

// 添加单元测试
it('should return empty array when cache miss', () => {
  cache.clear();
  const result = processItems('test-key');
  expect(result).toEqual([]);
});
```

---

## 6. 交付清单

| 检查项 | 状态 | 备注 |
|--------|------|------|
| ☐ 零号病人已定位 | | 具体到文件:行号 |
| ☐ 必然性已证明 | | 逻辑闭环无漏洞 |
| ☐ 证据已获取 | | 命令输出/变量值 |
| ☐ 修复 diff 已提供 | | 改动最小化 |
| ☐ 防复发测试已设计 | | Assert/单元测试 |

---

## Verdict

**[PASS]** / **[FAIL]**

**理由**：[只允许引用证据]
