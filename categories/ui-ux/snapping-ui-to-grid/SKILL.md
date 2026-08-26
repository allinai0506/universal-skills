---
name: snapping-ui-to-grid
description: Use when building, modifying, or reviewing any page-level UI layout — list pages, form pages, dashboards, drawers, or modal content. Triggers include new page scaffolds, UI/UX polish passes, review comments about misaligned edges, uneven toolbar control heights, ragged number columns, misplaced primary buttons, or arbitrary spacing values.
---

# Snapping UI to Grid（基准线对齐 + 视线动线分区）

## Overview

核心原则：**页面上每个元素都吸附在四条数学基准线上，每个功能固定在一个动线分区内。**
高级感不是装饰出来的，是「零意外对齐」累积出来的。

**项目适配**：间距 token、色板、字体、控件高度以各项目自己的设计系统为准（如设计规范文档 + 主题 Token 文件），本技能只规定它们通常未覆盖的**布局纪律**。示例适配：NexusArchive 用 `DESIGN.md`（8px 单位）+ antd `theme.ts`（Button controlHeight=36）。

## 四条基准线（输出契约）

### 1. 左轴 Left Axis —— 全页面只有一条左起线

面包屑首项、页面 H1、副标题、表格首列内容、表单第一个标签，必须落在同一条 X 上。

```css
/* 页面容器 */ .page { padding: 24px 32px; }
/* 卡片内表格：首/末单元格 padding 补偿边框，使内容与 H1 同线 */
td:first-child, th:first-child { padding-left: 31px; }  /* 32 − 1px border */
```

| 场景 | 实现 |
|------|------|
| Tailwind | 容器 `px-8`(32px)；表格首列 `pl-[31px]` 或卡片去水平 padding |
| antd Table | 自定义首列单元格 className，覆盖 `padding-inline-start` |

❌ 断裂症状：页面头 24px、表格首列 16px 内缩 → 两条假左轴，扫视时视线反复对焦。

### 2. 右轴 Right Axis —— 操作的终点线

页面级按钮组次序恒为 **[次要…主要]**，Primary CTA 永远最右、贴右缘；表格操作列右对齐；分页器靠右。三个右缘共享同一条线。

```tsx
<div className="flex justify-end gap-3">
  <Button>导出 CSV</Button>          {/* 次要在前 */}
  <Button type="primary">批量归档上传</Button>  {/* 主操作贴右轴 */}
</div>
```

❌ `[primary][secondary]` 左主右次 = 主按钮脱离右轴终点（基线测试 3/3 犯此错）。

### 3. 工具栏轴线 Toolbar Y-Center

同一工具栏内所有控件（Tabs、Input、Select、DatePicker、图标按钮）**高度统一、中轴线水平**：

- antd 类组件库：整条工具栏统一 `size`；默认高度跟随项目主题 token（NexusArchive 为 36px）。如需紧凑档位，先在 ConfigProvider 显式配置对应 `controlHeightSM` 等 token，再整条切换——禁止默认档与小尺寸混排。
- 手写 CSS/Tailwind：全部用同一高度 token（`h-9`=36），容器 `flex items-center`。

❌ Tabs 29px、输入框 34px、按钮 38px 高低参差。

### 4. 数字轴 Numeric Right-Align Axis（财务生命线）

金额、数量列：**右对齐 + 等宽字体 + `tabular-nums`**，表头同步右对齐。

| 场景 | 实现 |
|------|------|
| CSS | `.num { text-align:right; font-family:'JetBrains Mono',monospace; font-variant-numeric:tabular-nums; }` |
| antd | `column.align:'right'` + render 包 `<span className="font-mono tabular-nums">` |

让 340.00 与 1,250,000.00 的小数点在同一竖列，财务人员才能纵向扫出量级差。

## 五大动线分区（Quick Reference）

F 型扫描 + 古腾堡法则：视线从左上进入、右上落地行动、最终归宿右下。

| 分区 | 位置 | 只允许放 |
|------|------|----------|
| 认知定位区 | 左上 | 面包屑、H1、副标题（不放操作） |
| 核心行动区 | 右上 | 唯一 Primary CTA + 少量次要按钮 |
| 检索漏斗区 | 中部横条 | 状态 Tabs、日期筛选、搜索框、列设置 |
| 高密度工作区 | 中央 | 表格、预览、表单主体 |
| 终态确认区 | 右下 | 分页器、表单保存/提交 |

## 间距白名单

只允许设计系统 spacing token：4 / 8 / 16 / 24 / 32 / 48 / 64 px（Tailwind `p-1 p-2 p-4 p-6 p-8 p-12 p-16`）。
裸值 5、6、7、9、11、13、14px 一律视为违规，就近吸附到白名单值。

## Common Mistakes（基线实测高频失败）

| 症状 | 根因 |
|------|------|
| 页面标题与表格首列错位 8–16px | 单元格默认内边距未补偿容器 padding |
| 主按钮出现在按钮组左侧 | 未按「次要→主要」排列，右轴失守 |
| 工具栏控件高低参差 | 各控件独立设高，未锚定同一高度 token |
| 金额小数点竖向不对齐 | 缺 mono 字体或缺 `tabular-nums`，或列未右对齐 |
| margin/gap 出现 7px、13px | 脱离 8pt 白名单自由发挥 |

## 提交前自查

1. 截一条竖线从 H1 往下——是否穿过表格首列文字？
2. 最右元素（CTA/操作列/分页器）是否共享同一条右缘？
3. 工具栏所有控件高度是否同一个数值？
4. 金额列小数点是否成一条竖线？
5. 运行 `grep -E '(padding|margin|gap)[^:;}]*:[^;}]*[^0-9.](5|6|7|9|11|13|14)px'` 是否有命中？（只匹配间距属性，不会误报字号）
