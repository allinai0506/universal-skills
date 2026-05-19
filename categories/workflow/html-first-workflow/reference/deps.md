# External Dependencies (CDN)

Add inside `<head>`. Only load what you actually use.

## Tailwind CSS (required)

```html
<script src="https://cdn.tailwindcss.com"></script>
```

## Alpine.js (for tabs / accordion / toggle)

```html
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

## Mermaid (for diagrams)

```html
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({ startOnLoad: true, theme: 'default' });</script>
```

See `../mermaid-guide.md` for diagram patterns.

## Chart.js (for charts)

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

## Highlight.js (for code syntax highlighting)

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github-dark.min.css">
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/core.min.js"></script>
```
