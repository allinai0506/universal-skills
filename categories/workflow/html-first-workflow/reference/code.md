# Code Components

## Code Block (with filename + copy button)

```html
<div class="relative rounded-lg bg-gray-900 dark:bg-gray-950 overflow-hidden">
  <div class="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
    <span class="text-xs text-gray-400">filename.ts</span>
    <button onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.textContent)"
            class="text-xs text-gray-400 hover:text-white">复制</button>
  </div>
  <pre class="p-4 text-sm text-gray-100 overflow-x-auto"><code>// Code here...</code></pre>
</div>
```

## Inline Code

```html
<code class="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-sm font-mono text-primary">inline_code</code>
```

## Diff View

```html
<div class="rounded-lg bg-gray-900 overflow-hidden text-sm">
  <div class="px-4 py-2 bg-red-900/30 text-red-300">- 删除的行</div>
  <div class="px-4 py-2 bg-green-900/30 text-green-300">+ 添加的行</div>
  <div class="px-4 py-2 text-gray-300">  未修改</div>
</div>
```
