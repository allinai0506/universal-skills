# Component Reference — Index

Load only the files you need. Do NOT read the whole reference.

| Need | File | Components |
|------|------|------------|
| **Start here — base template** | `skeleton.md` | **Complete HTML with Tailwind CDN, dark mode, print CSS, nav, cover, TOC sidebar** |
| Page shell, nav, sidebar, footer, hero | `layout.md` | Full template, nav bar, sidebar, breadcrumb, step indicator, cover/hero, footer |
| Info/warning/error/success boxes | `feedback.md` | Section header, info box, warning, alert, success, toast, spinner, progress |
| Card grids, stat cards, icon cards | `cards.md` | Basic card, icon card, feature grid, stat card |
| Tabs, accordion, collapsible, toggle | `interactive.md` | Tabs (Alpine), collapsible (native), accordion, toggle switch |
| Tables, MoSCoW matrix, checklist, timeline | `data.md` | Table, priority matrix, checklist, timeline |
| Code blocks, diff view, inline code | `code.md` | Code block, inline code, diff view |
| Inputs, selects, forms | `forms.md` | Input, select |
| Status badges, severity badges | `status.md` | Status badge, severity badge |
| CDN imports (Tailwind, Alpine, Mermaid, Chart.js) | `deps.md` | External dependencies |

## Loading Strategy

1. Always start from `skeleton.md` — it includes the complete HTML shell. Then supplement with specific components.
2. Pick 1-3 additional files based on document type:
   - **Spec / PRD** → `cards.md` + `data.md` + `feedback.md`
   - **Code review** → `feedback.md` + `status.md` + `code.md`
   - **Report** → `cards.md` + `data.md` + `status.md`
   - **Comparison** → `interactive.md` + `data.md`
   - **SOP** → `interactive.md` + `feedback.md`
3. Add `deps.md` only if you need Alpine.js, Mermaid, or Chart.js.

Components are copy-paste ready. Adapt Tailwind classes for your color scheme; do NOT remove `dark:` variants.
