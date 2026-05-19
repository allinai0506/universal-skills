# Layout Components

## Complete HTML Template

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Document Title</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            primary: '#3B82F6',
          }
        }
      }
    }
  </script>
  <style>
    @media print {
      .no-print { display: none !important; }
      .print-break { page-break-before: always; }
      body { background: white !important; color: black !important; }
    }
  </style>
</head>
<body class="bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-gray-100 min-h-screen">

  <!-- Navigation Bar -->
  <nav class="sticky top-0 z-50 bg-white/80 dark:bg-gray-800/80 backdrop-blur border-b">
    <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <h1 class="text-xl font-bold text-primary">Document Title</h1>
        <span class="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-700">v1.0</span>
      </div>
      <div class="flex gap-2">
        <button onclick="toggleDark()" class="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700" title="切换主题">🌓</button>
        <button onclick="window.print()" class="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700" title="打印">🖨️</button>
        <button onclick="exportMd()" class="px-3 py-1 rounded bg-primary text-white text-sm">📥 导出 MD</button>
      </div>
    </div>
  </nav>

  <div class="flex">
    <!-- Sidebar -->
    <aside class="hidden lg:block w-64 fixed h-[calc(100vh-4rem)] overflow-y-auto p-4 border-r bg-white/50 dark:bg-gray-900/50">
      <div class="text-xs font-semibold text-gray-500 uppercase mb-3">目录</div>
      <nav class="space-y-1 text-sm">
        <a href="#overview" class="block px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800">概览</a>
        <a href="#details" class="block px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800">详情</a>
        <a href="#examples" class="block px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800">示例</a>
      </nav>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 lg:ml-64 p-8 max-w-4xl">
      <!-- Content sections -->
    </main>
  </div>

  <script>
    function toggleDark() {
      document.documentElement.classList.toggle('dark');
    }
    function exportMd() {
      alert('导出功能实现中...');
    }
  </script>
</body>
</html>
```

## Breadcrumb

```html
<nav class="flex text-sm text-gray-500 mb-6">
  <a href="#" class="hover:text-primary">首页</a>
  <span class="mx-2">/</span>
  <a href="#" class="hover:text-primary">文档</a>
  <span class="mx-2">/</span>
  <span class="text-gray-900 dark:text-gray-100">当前页</span>
</nav>
```

## Step Indicator

```html
<div class="flex items-center gap-2 mb-8">
  <div class="flex items-center">
    <div class="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold">1</div>
    <span class="ml-2 font-medium">步骤一</span>
  </div>
  <div class="flex-1 h-0.5 bg-gray-300 mx-4"></div>
  <div class="flex items-center">
    <div class="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold">2</div>
    <span class="ml-2 font-medium">步骤二</span>
  </div>
  <div class="flex-1 h-0.5 bg-gray-300 mx-4"></div>
  <div class="flex items-center">
    <div class="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center font-bold">3</div>
    <span class="ml-2 text-gray-500">步骤三</span>
  </div>
</div>
```

## Section Header

```html
<section class="mb-12">
  <div class="flex items-center gap-3 mb-4">
    <div class="w-1 h-8 bg-primary rounded"></div>
    <h2 class="text-2xl font-bold">章节标题</h2>
  </div>
  <p class="text-gray-600 dark:text-gray-400">章节描述...</p>
</section>
```

## Cover / Hero Section

```html
<section class="text-center py-16 px-4 bg-gradient-to-b from-primary/10 to-transparent rounded-b-3xl">
  <div class="inline-block px-4 py-1 rounded-full bg-primary/10 text-primary text-sm mb-4">v1.0 Draft</div>
  <h1 class="text-4xl md:text-5xl font-bold mb-4">项目名称</h1>
  <p class="text-xl text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
    简短的描述文字，说明这个文档的目的和范围
  </p>
  <div class="flex flex-wrap justify-center gap-4 text-sm text-gray-500">
    <span>📅 2026-05-12</span>
    <span>👤 作者</span>
    <span>📁 docs/specs/</span>
  </div>
</section>
```

## Footer

```html
<footer class="mt-16 py-8 border-t text-center text-sm text-gray-500">
  <p>最后更新于 2026-05-12 | 由 AI Agent 生成</p>
  <p class="mt-1">HTML-First Documentation Workflow</p>
</footer>
```
