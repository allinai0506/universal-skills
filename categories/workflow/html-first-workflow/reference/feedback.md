# Feedback Components

## Info Box

```html
<div class="p-4 rounded-lg bg-blue-50 border-l-4 border-blue-500 dark:bg-blue-900/30 mb-6">
  <div class="flex items-start gap-3">
    <span class="text-2xl">💡</span>
    <div>
      <h4 class="font-semibold text-blue-900 dark:text-blue-100">提示</h4>
      <p class="text-blue-800 dark:text-blue-200 mt-1">这里是提示内容...</p>
    </div>
  </div>
</div>
```

## Warning Box

```html
<div class="p-4 rounded-lg bg-yellow-50 border-l-4 border-yellow-500 dark:bg-yellow-900/30 mb-6">
  <div class="flex items-start gap-3">
    <span class="text-2xl">⚠️</span>
    <div>
      <h4 class="font-semibold text-yellow-900 dark:text-yellow-100">注意</h4>
      <p class="text-yellow-800 dark:text-yellow-200 mt-1">这里是警告内容...</p>
    </div>
  </div>
</div>
```

## Alert / Error Box

```html
<div class="p-4 rounded-lg bg-red-50 border-l-4 border-red-500 dark:bg-red-900/30 mb-6">
  <div class="flex items-start gap-3">
    <span class="text-2xl">🚨</span>
    <div>
      <h4 class="font-semibold text-red-900 dark:text-red-100">错误</h4>
      <p class="text-red-800 dark:text-red-200 mt-1">这里是错误内容...</p>
    </div>
  </div>
</div>
```

## Success Box

```html
<div class="p-4 rounded-lg bg-green-50 border-l-4 border-green-500 dark:bg-green-900/30 mb-6">
  <div class="flex items-start gap-3">
    <span class="text-2xl">✅</span>
    <div>
      <h4 class="font-semibold text-green-900 dark:text-green-100">成功</h4>
      <p class="text-green-800 dark:text-green-200 mt-1">这里是成功内容...</p>
    </div>
  </div>
</div>
```

## Toast Notification

```html
<div class="fixed bottom-4 right-4 p-4 rounded-lg shadow-lg bg-gray-800 text-white flex items-center gap-3">
  <span class="text-lg">✓</span>
  <span>操作成功</span>
</div>
```

## Loading Spinner

```html
<div class="flex items-center justify-center p-8">
  <div class="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
</div>
```

## Progress Bar

```html
<div>
  <div class="flex justify-between text-sm mb-1">
    <span>进度</span>
    <span>75%</span>
  </div>
  <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
    <div class="h-full bg-primary rounded-full transition-all" style="width: 75%"></div>
  </div>
</div>
```
