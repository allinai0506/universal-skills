# Data Display Components

## Table

```html
<div class="overflow-x-auto rounded-lg border">
  <table class="w-full text-sm">
    <thead class="bg-gray-50 dark:bg-gray-800">
      <tr>
        <th class="px-4 py-3 text-left font-semibold">名称</th>
        <th class="px-4 py-3 text-left font-semibold">状态</th>
        <th class="px-4 py-3 text-left font-semibold">更新时间</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
      <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
        <td class="px-4 py-3">项目 A</td>
        <td class="px-4 py-3"><span class="px-2 py-1 rounded text-xs bg-green-100 text-green-800">进行中</span></td>
        <td class="px-4 py-3 text-gray-500">2026-05-12</td>
      </tr>
      <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
        <td class="px-4 py-3">项目 B</td>
        <td class="px-4 py-3"><span class="px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-800">待审核</span></td>
        <td class="px-4 py-3 text-gray-500">2026-05-10</td>
      </tr>
    </tbody>
  </table>
</div>
```

## Comparison Table (highlighted columns)

```html
<table class="w-full">
  <thead>
    <tr>
      <th>Feature</th>
      <th class="bg-green-100">Option A</th>
      <th class="bg-blue-100">Option B</th>
    </tr>
  </thead>
  <tbody>
    <!-- Comparison rows -->
  </tbody>
</table>
```

## Priority Matrix (MoSCoW)

```html
<div class="grid grid-cols-4 gap-4">
  <div class="p-4 rounded-lg bg-red-100 dark:bg-red-900/30 border-2 border-red-300">
    <h4 class="font-bold text-red-900 dark:text-red-100 mb-2">Must Have</h4>
    <ul class="text-sm space-y-1">
      <li>• 功能 1</li>
      <li>• 功能 2</li>
    </ul>
  </div>
  <div class="p-4 rounded-lg bg-orange-100 dark:bg-orange-900/30 border-2 border-orange-300">
    <h4 class="font-bold text-orange-900 dark:text-orange-100 mb-2">Should Have</h4>
    <ul class="text-sm space-y-1">
      <li>• 功能 3</li>
    </ul>
  </div>
  <div class="p-4 rounded-lg bg-blue-100 dark:bg-blue-900/30 border-2 border-blue-300">
    <h4 class="font-bold text-blue-900 dark:text-blue-100 mb-2">Could Have</h4>
    <ul class="text-sm space-y-1">
      <li>• 功能 4</li>
    </ul>
  </div>
  <div class="p-4 rounded-lg bg-gray-100 dark:bg-gray-800 border-2 border-gray-300">
    <h4 class="font-bold text-gray-700 dark:text-gray-300 mb-2">Won't Have</h4>
    <ul class="text-sm space-y-1 text-gray-500">
      <li>• 功能 5</li>
    </ul>
  </div>
</div>
```

## Checklist

```html
<div class="space-y-2">
  <label class="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50">
    <input type="checkbox" class="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary">
    <span>已完成的任务</span>
  </label>
  <label class="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50">
    <input type="checkbox" class="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary">
    <span>待办的任务</span>
  </label>
</div>
```

## Timeline

```html
<div class="relative border-l-2 border-gray-300 dark:border-gray-600 ml-4 space-y-8">
  <div class="relative pl-8">
    <div class="absolute left-[-9px] w-4 h-4 rounded-full bg-primary border-4 border-white dark:border-gray-900"></div>
    <div class="font-semibold">2026-05-12</div>
    <div class="text-gray-600 dark:text-gray-400 mt-1">完成第一阶段开发</div>
  </div>
  <div class="relative pl-8">
    <div class="absolute left-[-9px] w-4 h-4 rounded-full bg-gray-400 border-4 border-white dark:border-gray-900"></div>
    <div class="font-semibold">2026-05-15 (计划)</div>
    <div class="text-gray-600 dark:text-gray-400 mt-1">开始第二阶段</div>
  </div>
</div>
```
