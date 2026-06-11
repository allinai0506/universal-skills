---
name: linear-task-creator
description: Use when the user mentions Linear, wants to create/update a task, says "记到 Linear", "加个 task", "开个任务", or mentions "林哥". Creates or updates Linear issues with structured project templates.
---

# Linear Task Creator Skill

## 触发暗语
- "记到 Linear" / "加个 task" / "开个任务"
- "林哥"

## 执行流程

1. 通过用户描述获取任务信息（标题、背景、要点）
2. 按以下模板补全结构化内容后，调用 Linear GraphQL API 创建/更新 issue

## Issue 模板

```markdown
## 背景
{为什么需要这个任务}

## 问题
{具体要解决什么}

## 设计决策
1. {方案1 — 理由}
2. {方案2 — 理由}
3. ...

## 改动清单

### 后端
- {文件名} — {改什么}
- ...

### 前端
- {文件名} — {改什么}
- ...

### 数据库
- {migration 描述}

## 关键接口
- {接口路径} {请求/响应格式}

## 兼容性
- {存量数据怎么处理}
- {回退方案}

## 测试要点
1. {场景1}
2. {场景2}
...

## 风险
1. {风险 + 缓解措施}
2. ...
```

## API 调用方式

```bash
# 创建 issue
curl -s -X POST https://api.linear.app/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: $LINEAR_API_KEY" \
  -d '{
    "query": "mutation { issueCreate(input: { title: \"...\", description: \"...\", projectId: \"f3e05cbb-9d2a-43f8-807a-dc35824f532f\", teamId: \"1a5764b2-2cda-4954-824b-2e43dc557d14\" }) { issue { id url identifier } } }"
  }'

# 更新 issue
curl -s -X POST https://api.linear.app/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: $LINEAR_API_KEY" \
  -d '{
    "query": "mutation { issueUpdate(id: \"...\", input: { description: \"...\" }) { issue { id url identifier } } }"
  }'
```

## 固定参数
- projectId: `f3e05cbb-9d2a-43f8-807a-dc35824f532f`（西域项目）
- teamId: `1a5764b2-2cda-4954-824b-2e43dc557d14`（Ericforai 团队）
- Authorization: `$LINEAR_API_KEY` 环境变量
