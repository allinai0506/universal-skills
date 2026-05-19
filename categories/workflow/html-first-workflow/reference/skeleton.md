# HTML Skeleton — Base Template

Copy this complete skeleton as your starting point. Add components from other reference files as needed.

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>文档标题 — 副标题</title>

  <!-- Tailwind CSS (required) -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- Alpine.js (for tabs, accordion — only if needed) -->
  <!-- <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script> -->

  <!-- Mermaid (for diagrams — only if needed) -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({ startOnLoad: true, theme: 'default' });</script> -->

  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: { primary: '#3B82F6' }
        }
      }
    }
  </script>
  <style>
    /* Print: hide nav, sidebar, buttons; ensure readable on paper */
    @media print {
      .no-print { display: none !important; }
      .print-break { page-break-before: always; }
      body { background: white !important; color: black !important; }
      nav, aside, footer, button { display: none !important; }
      main { margin-left: 0 !important; padding: 0 !important; max-width: 100% !important; }
      @page { margin: 2cm; }
    }
    /* Smooth scrolling for TOC links */
    html { scroll-behavior: smooth; }
    /* Ensure x-cloak works with Alpine (if loaded) */
    [x-cloak] { display: none !important; }
  </style>
</head>
<body class="bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-gray-100 min-h-screen">

  <!-- ═══════════════════════════════════════════════════════════
       NAVIGATION BAR (sticky, no-print)
       ═══════════════════════════════════════════════════════════ -->
  <nav class="sticky top-0 z-50 bg-white/80 dark:bg-gray-800/80 backdrop-blur border-b no-print">
    <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <h1 class="text-lg font-bold text-primary truncate max-w-md">文档标题</h1>
        <span class="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">v1.0</span>
        <span class="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300">草稿</span>
      </div>
      <div class="flex items-center gap-1">
        <button onclick="document.documentElement.classList.toggle('dark')" class="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 text-lg" title="切换主题">🌓</button>
        <button onclick="window.print()" class="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 text-lg" title="打印/导出 PDF">🖨️</button>
        <button onclick="window.scrollTo({top:0,behavior:'smooth'})" class="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 text-lg" title="回到顶部">⬆️</button>
      </div>
    </div>
  </nav>

  <div class="flex max-w-7xl mx-auto">

    <!-- ════════════════════════════════════════════════════════════
         TABLE OF CONTENTS — sidebar (lg+ only, no-print)
         ════════════════════════════════════════════════════════════ -->
    <aside class="hidden lg:block w-56 xl:w-64 flex-shrink-0 border-r min-h-[calc(100vh-4rem)] no-print">
      <div class="sticky top-16 p-4 overflow-y-auto max-h-[calc(100vh-5rem)]">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">目录</p>
        <nav class="space-y-0.5 text-sm" id="toc">
          <!-- Fill in by hand. Example:
          <a href="#overview" class="block px-3 py-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 hover:text-primary transition-colors">概览</a>
          <a href="#details" class="block px-3 py-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 hover:text-primary transition-colors">详情</a>
          -->
        </nav>
      </div>
    </aside>

    <!-- ════════════════════════════════════════════════════════════
         MAIN CONTENT
         ════════════════════════════════════════════════════════════ -->
    <main class="flex-1 min-w-0 p-6 md:p-8 xl:p-10 max-w-4xl">

      <!-- ===== COVER / HERO ===== -->
      <section class="text-center py-12 md:py-16 px-4 bg-gradient-to-b from-primary/5 to-transparent rounded-2xl mb-10">
        <div class="inline-block px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium mb-4">v1.0 · 草稿</div>
        <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold mb-4">文档标题</h1>
        <p class="text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto mb-8">
          简短描述，说明本文档的目的、读者和适用范围
        </p>
        <div class="flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-gray-400">
          <span>📅 2026-05-19</span>
          <span>✍️ 作者 / 团队</span>
          <span>📁 docs/artifacts/</span>
          <span>🔄 v1.0</span>
        </div>
      </section>

      <!-- ===== CONTENT SECTIONS ===== -->
      <!-- Add your sections here. Use the following pattern:

      <section id="section-id" class="mb-12 scroll-mt-20">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-1 h-7 bg-primary rounded-full"></div>
          <h2 class="text-2xl font-bold">章节标题</h2>
        </div>
        <p class="text-gray-600 dark:text-gray-400 mb-4">章节描述...</p>
      </section>

      -->

    </main>
  </div>

  <!-- ════════════════════════════════════════════════════════════
       FOOTER
       ════════════════════════════════════════════════════════════ -->
  <footer class="border-t py-6 text-center text-sm text-gray-400 no-print">
    <p>最后由 AI Agent 于 2026-05-19 生成 · HTML-First Documentation Workflow</p>
  </footer>

</body>
</html>
```

## Usage

1. Copy the skeleton as-is.
2. Add CDN scripts for Alpine/Mermaid/Chart.js by uncommenting the `<script>` tags (only what you need).
3. Replace `文档标题`, `副标题`, `作者 / 团队`, and other placeholders.
4. Set the status badge text/color (`草稿`/`评审中`/`已定稿`):
   - Draft (草稿): `bg-yellow-100 text-yellow-800`
   - Review (评审中): `bg-blue-100 text-blue-800`
   - Approved (已定稿): `bg-green-100 text-green-800`
5. Add TOC links in `<nav id="toc">` — each `#section-id` must match a `scroll-mt-20` on the section.
6. Add content sections following the commented pattern.
7. Save to `docs/artifacts/`.

## Print Behavior

- `nav`, `aside`, `footer`, and all elements with `.no-print` are hidden on print/PDF
- Use `.print-break` on elements that should start on a new page
- The `@media print` block strips backgrounds, forcing black text on white
