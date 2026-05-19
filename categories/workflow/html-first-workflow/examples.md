# HTML-First Workflow - Examples

## Quick Start Example

**User**: "我需要一个用户认证模块的需求文档"

**Agent Response**: Generate a complete HTML requirements document saved to `docs/artifacts/auth-requirements-v1-20260512.html`

**Output includes**:
- Cover section (title, version, date, status badge)
- Objectives & Scope
- User stories (login, register, password reset, OAuth)
- Functional specs (collapsible modules)
- Non-functional requirements (performance, security)
- Data model (ER diagram with Mermaid)
- Risk matrix
- MoSCoW priority matrix

---

## Example 1: Requirements Document

**Trigger**: "生成需求", "写PRD", "写规格", "功能需求"

```html
<!-- Structure -->
- Cover with project title, version, author
- Table of contents (sticky sidebar)
- Executive summary
- User stories grid (cards)
- Functional requirements (accordion by module)
- Non-functional requirements (performance, security, scalability)
- Data model (ER diagram)
- Risks & assumptions
- MoSCoW priority matrix
- Timeline/gantt chart
```

---

## Example 2: Code Review Report

**Trigger**: "/review", "审查代码", "代码审查", "PR审查"

```html
<!-- Structure -->
- PR overview (files changed, lines added/removed)
- Module dependency map
- Key changes with inline annotations
- Risk highlights:
  - 🔴 Critical issues
  - 🟠 High priority
  - 🟡 Warnings
- Suggestions:
  - Performance improvements
  - Security considerations
  - Code style
- Test coverage analysis
- Review summary
```

---

## Example 3: Architecture Document

**Trigger**: "架构设计", "系统设计", "画架构图", "/spec"

```html
<!-- Structure -->
- Executive summary
- Architecture overview (Mermaid graph)
- Component details (cards)
- Data flow (sequence diagram)
- API design
- Technology stack comparison (tabs)
- Deployment architecture
- Security considerations
- Risks & trade-offs
- Future scalability
```

---

## Example 4: Multi-Option Exploration

**Trigger**: "/explore", "方案对比", "技术选型", "选哪个好"

```html
<!-- Structure -->
- Problem statement
- Options tabs (Option A | Option B | Option C)
- Comparison table
- Pros/cons cards
- Use case matrix
- Risk assessment
- Recommendation
- Implementation effort estimate
```

---

## Example 5: Weekly Status Report

**Trigger**: "/report", "周报", "月报", "季度总结"

```html
<!-- Structure -->
- Week/period header
- Key metrics (stat cards grid)
- Completed tasks (timeline)
- In progress (kanban cards)
- Blockers & risks
- Next week plan (checklist)
- Team highlights
- Charts (burndown, velocity)
```

---

## Example 6: Meeting Notes

**Trigger**: "会议纪要", "meeting notes", "记录"

```html
<!-- Structure -->
- Meeting header (date, attendees, topic)
- Agenda (step indicator)
- Discussion points (collapsible)
- Decisions made (highlighted)
- Action items (checklist with owners)
- Next meeting info
- Related documents
```

---

## Example 7: SOP (Standard Operating Procedure)

**Trigger**: "/sop", "标准流程", "操作手册", "SOP"

```html
<!-- Structure -->
- Purpose & scope
- Prerequisites
- Step-by-step guide (numbered, with screenshots)
- Decision tree (flowchart)
- Troubleshooting section
- FAQ (accordion)
- Related procedures
- Version history
```

---

## Example 8: Competitive Analysis

**Trigger**: "竞品分析", "竞争对手", "对比分析"

```html
<!-- Structure -->
- Executive summary
- Market overview
- Competitor comparison (table)
- Feature matrix (grid)
- Pricing comparison
- Strengths/weaknesses radar chart
- User reviews synthesis
- Our advantages
- Recommendations
```

---

## Example 9: API Documentation

**Trigger**: "API文档", "接口文档", "接口设计"

```html
<!-- Structure -->
- Overview
- Authentication
- Endpoints (tabbed by resource)
- Request/response examples
- Error codes table
- Rate limiting
- SDK examples (tabs by language)
- Postman collection link
```

---

## Example 10: Data Model Design

**Trigger**: "数据模型", "数据库设计", "ER图"

```html
<!-- Structure -->
- Overview
- Entity definitions
- ER diagram (Mermaid)
- Table schemas
- Relationships
- Indexes
- Constraints
- Migration strategy
```

---

## Common Patterns

### Card Grid Layout

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <!-- Cards go here -->
</div>
```

### Comparison Table

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

### Timeline with Milestones

```html
<div class="relative border-l-2 border-primary ml-4">
  <div class="mb-8 pl-8 relative">
    <div class="absolute left-[-25px] w-6 h-6 rounded-full bg-primary border-4 border-white"></div>
    <div class="font-bold">Phase 1</div>
    <div class="text-gray-500">2025-Q1</div>
  </div>
  <!-- More timeline items -->
</div>
```

### Stat Dashboard

```html
<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
  <div class="p-6 bg-white dark:bg-gray-800 rounded-xl border">
    <p class="text-sm text-gray-500">总用户</p>
    <p class="text-3xl font-bold">12,345</p>
    <p class="text-sm text-green-600">↑ 15%</p>
  </div>
  <!-- More stats -->
</div>
```
