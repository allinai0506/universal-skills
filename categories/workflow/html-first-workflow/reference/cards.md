# Card Components

## Basic Card

```html
<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
  <h3 class="text-lg font-semibold mb-2">卡片标题</h3>
  <p class="text-gray-600 dark:text-gray-400">卡片内容...</p>
</div>
```

## Card with Icon

```html
<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
  <div class="flex items-start gap-4">
    <div class="p-3 rounded-lg bg-primary/10">
      <span class="text-2xl">📦</span>
    </div>
    <div class="flex-1">
      <h3 class="text-lg font-semibold mb-1">功能模块</h3>
      <p class="text-sm text-gray-600 dark:text-gray-400">模块描述...</p>
    </div>
  </div>
</div>
```

## Feature Card Grid

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6 hover:shadow-md transition-shadow">
    <div class="text-3xl mb-4">🚀</div>
    <h3 class="font-semibold mb-2">高性能</h3>
    <p class="text-sm text-gray-600 dark:text-gray-400">描述内容...</p>
  </div>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6 hover:shadow-md transition-shadow">
    <div class="text-3xl mb-4">🔒</div>
    <h3 class="font-semibold mb-2">安全可靠</h3>
    <p class="text-sm text-gray-600 dark:text-gray-400">描述内容...</p>
  </div>
  <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6 hover:shadow-md transition-shadow">
    <div class="text-3xl mb-4">⚡</div>
    <h3 class="font-semibold mb-2">快速响应</h3>
    <p class="text-sm text-gray-600 dark:text-gray-400">描述内容...</p>
  </div>
</div>
```

## Stat Card

```html
<div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-6">
  <p class="text-sm text-gray-500 mb-1">总用户数</p>
  <p class="text-3xl font-bold text-primary">12,345</p>
  <p class="text-sm text-green-600 mt-2">↑ 12.5% 较上周</p>
</div>
```

## Stat Dashboard Grid

```html
<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
  <div class="p-6 bg-white dark:bg-gray-800 rounded-xl border">
    <p class="text-sm text-gray-500">总用户</p>
    <p class="text-3xl font-bold">12,345</p>
    <p class="text-sm text-green-600">↑ 15%</p>
  </div>
  <!-- Repeat for other stats -->
</div>
```
