<!--
  追加到 docs/lessons/<tech>-gotchas.md 末尾，或新建文件。
  新建时文件头加：
  # <Tech> 陷阱与调试经验
  记录开发过程中遇到的 <Tech> 陷阱、调试方法论和设计教训。
  不写 wiki frontmatter；docs 是原始文档层。
-->

## N. <陷阱标题：如"el-upload on-change 绑定陷阱">

### 问题

```vue
<!-- ❌ 错误：<一句话说明为什么错> -->
<错误代码>

<!-- ✅ 正确：<一句话说明正确做法> -->
<正确代码>
```

<详细解释：为什么错误写法会导致问题，背后机制是什么。>

### 正确写法

```vue
<script setup>
<完整可复制的正确代码>
</script>

<template>
  <正确用法>
</template>
```

### 调试方法

<如果怀疑此类问题，如何定位：>

```javascript
<调试代码，如加日志>
```

<或者：用 Vue DevTools 检查 XX / 用浏览器 Network 面板看 XX>
