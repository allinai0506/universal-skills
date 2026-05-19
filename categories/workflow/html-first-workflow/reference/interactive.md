# Interactive Components

Requires Alpine.js for tabs/accordion. See `deps.md`.

## Tabs (Alpine.js)

```html
<div x-data="{ activeTab: 'tab1' }">
  <div class="flex border-b border-gray-200 dark:border-gray-700 mb-6">
    <button @click="activeTab = 'tab1'"
            :class="activeTab === 'tab1' ? 'border-primary text-primary' : 'text-gray-500 hover:text-gray-700'"
            class="px-4 py-2 border-b-2 -mb-px font-medium">
      选项一
    </button>
    <button @click="activeTab = 'tab2'"
            :class="activeTab === 'tab2' ? 'border-primary text-primary' : 'text-gray-500 hover:text-gray-700'"
            class="px-4 py-2 border-b-2 -mb-px font-medium">
      选项二
    </button>
  </div>
  <div x-show="activeTab === 'tab1'" class="prose dark:prose-invert">
    <p>选项一的内容...</p>
  </div>
  <div x-show="activeTab === 'tab2'" class="prose dark:prose-invert" x-cloak>
    <p>选项二的内容...</p>
  </div>
</div>
```

## Collapsible (HTML native, no JS)

```html
<details class="bg-white dark:bg-gray-800 rounded-lg border group mb-4">
  <summary class="p-4 cursor-pointer font-medium flex items-center justify-between">
    <span>可折叠的章节</span>
    <span class="transform transition-transform group-open:rotate-180">▼</span>
  </summary>
  <div class="p-4 pt-0 text-gray-600 dark:text-gray-400">
    折叠内容...
  </div>
</details>
```

## Accordion (Alpine.js, single-open)

```html
<div x-data="{ open: null }" class="space-y-2">
  <div class="bg-white dark:bg-gray-800 rounded-lg border">
    <button @click="open = open === 1 ? null : 1" class="w-full p-4 text-left font-medium flex justify-between items-center">
      <span>第一项</span>
      <span x-show="open !== 1">▶</span>
      <span x-show="open === 1" x-cloak>▼</span>
    </button>
    <div x-show="open === 1" x-cloak class="p-4 pt-0 text-gray-600 dark:text-gray-400">
      第一项内容...
    </div>
  </div>
  <div class="bg-white dark:bg-gray-800 rounded-lg border">
    <button @click="open = open === 2 ? null : 2" class="w-full p-4 text-left font-medium flex justify-between items-center">
      <span>第二项</span>
      <span x-show="open !== 2">▶</span>
      <span x-show="open === 2" x-cloak>▼</span>
    </button>
    <div x-show="open === 2" x-cloak class="p-4 pt-0 text-gray-600 dark:text-gray-400">
      第二项内容...
    </div>
  </div>
</div>
```

## Toggle Switch

```html
<div class="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg border">
  <span class="font-medium">启用功能</span>
  <button onclick="this.classList.toggle('bg-gray-200'); this.classList.toggle('bg-primary'); this.classList.toggle('bg-gray-300'); this.classList.toggle('dark:bg-gray-600')"
          class="relative w-12 h-6 rounded-full bg-gray-300 transition-colors">
    <span class="absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow transition-transform"></span>
  </button>
</div>
```
