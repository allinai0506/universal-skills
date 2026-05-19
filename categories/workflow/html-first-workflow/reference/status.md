# Status & Badge Components

## Status Badge

```html
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
  进行中
</span>
<!-- Variants -->
<span class="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">成功</span>
<span class="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">待处理</span>
<span class="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">失败</span>
<span class="bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">草稿</span>
```

## Severity Badge (for code review)

```html
<div class="space-y-2">
  <span class="inline-flex items-center px-3 py-1 rounded text-xs font-bold bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
    🔴 Critical
  </span>
  <span class="inline-flex items-center px-3 py-1 rounded text-xs font-bold bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
    🟠 High
  </span>
  <span class="inline-flex items-center px-3 py-1 rounded text-xs font-bold bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
    🟡 Medium
  </span>
  <span class="inline-flex items-center px-3 py-1 rounded text-xs font-bold bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
    🟢 Low
  </span>
</div>
```
