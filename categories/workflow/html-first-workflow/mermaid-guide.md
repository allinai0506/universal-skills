# Mermaid Diagram Best Practices

## Quick Start

```html
<!-- Include Mermaid -->
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({
    startOnLoad: true,
    theme: 'default',
    themeVariables: {
      primaryColor: '#3B82F6',
      primaryTextColor: '#1F2937',
      primaryBorderColor: '#3B82F6',
      lineColor: '#6B7280',
      secondaryColor: '#F3F4F6',
    }
  });
</script>
```

```html
<!-- Dark mode support -->
<script>
  function updateMermaidTheme() {
    const isDark = document.documentElement.classList.contains('dark');
    mermaid.initialize({
      theme: isDark ? 'dark' : 'default'
    });
  }
  // Call on theme toggle
</script>
```

---

## 1. Flowcharts

### Basic Flowchart

```html
<div class="mermaid">
graph TD
    A[开始] --> B{判断条件}
    B -->|条件1| C[执行操作1]
    B -->|条件2| D[执行操作2]
    C --> E[结束]
    D --> E
</div>
```

### Flowchart with Subgraphs

```html
<div class="mermaid">
graph TB
    subgraph 前端
        A[用户界面] --> B[表单提交]
    end
    subgraph 后端
        C[API接收] --> D[业务处理]
        D --> E[数据库操作]
    end
    subgraph 响应
        F[返回结果] --> G[更新界面]
    end
    B --> C
    E --> F
</div>
```

### Flowchart Best Practices

| Do | Don't |
|----|-------|
| Use `graph TD` (top-down) for vertical flow | Avoid crossing lines |
| Label edges clearly | Don't leave edges unlabeled |
| Keep nodes concise (< 20 chars) | Avoid overly complex graphs |
| Group related nodes with subgraphs | Don't exceed 20 nodes per graph |

---

## 2. Sequence Diagrams

### Basic Sequence

```html
<div class="mermaid">
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant A as API
    participant D as 数据库

    U->>F: 提交请求
    F->>A: POST /api/users
    A->>D: INSERT user
    D-->>A: 返回新用户
    A-->>F: 201 Created
    F-->>U: 显示成功
</div>
```

### Sequence with Loops and Conditions

```html
<div class="mermaid">
sequenceDiagram
    participant C as 客户端
    participant S as 服务器

    C->>S: 请求数据
    S->>S: 验证token
    alt token有效
        S-->>C: 返回数据
    else token无效
        S-->>C: 401 Unauthorized
        C->>S: 刷新token
        S-->>C: 新token
    end
</div>
```

### Sequence Diagram Syntax

```
->  : 实线箭头（同步调用）
--> : 虚线箭头（返回）
->> : 实线箭头（异步）
-->>: 虚线箭头（异步返回）
```

### Sequence Best Practices

| Element | Usage |
|---------|-------|
| `participant` | Define actors at top |
| `Note` | Add context/annotations |
| `loop` | Repeated actions |
| `alt/else` | Conditional paths |
| `opt` | Optional paths |

---

## 3. Class Diagrams

### Basic Class Structure

```html
<div class="mermaid">
classDiagram
    class User {
        -String name
        -String email
        +login()
        +logout()
        +getProfile()
    }

    class Order {
        -String id
        -Date createdAt
        +create()
        +cancel()
    }

    User "1" --> "*" Order : places
</div>
```

### Class Diagram with Inheritance

```html
<div class="mermaid">
classDiagram
    class Animal {
        +String name
        +makeSound()
    }

    class Dog {
        +bark()
    }

    class Cat {
        +meow()
    }

    class Bird {
        +fly()
    }

    Animal <|-- Dog
    Animal <|-- Cat
    Animal <|-- Bird
</div>
```

### Class Relationship Symbols

| Symbol | Meaning |
|--------|---------|
| `<|--` | Inheritance |
| `*--` | Composition |
| `o--` | Aggregation |
| `-->` | Association |
| `..>` | Dependency |
| `..|>` | Realization |

### Class Visibility

| Symbol | Meaning |
|--------|---------|
| `-` | Private |
| `+` | Public |
| `#` | Protected |
| `~` | Package |

---

## 4. State Diagrams

### Basic State Machine

```html
<div class="mermaid">
stateDiagram-v2
    [*] --> Draft: 创建
    Draft --> Review: 提交审核
    Review --> Draft: 退回修改
    Review --> Approved: 审核通过
    Approved --> Published: 发布
    Published --> [*]: 下线
    Draft --> [*]: 删除
</div>
```

### State with Activities

```html
<div class="mermaid">
stateDiagram-v2
    [*] --> Active

    state Active {
        [*] --> Working
        Working --> Paused: 暂停
        Paused --> Working: 继续
        Working --> [*]: 完成
    }
</div>
```

---

## 5. Entity Relationship (ER) Diagrams

### Basic ER Diagram

```html
<div class="mermaid">
erDiagram
    USER ||--o{ ORDER : places
    USER {
        uuid id PK
        string email
        string name
        datetime created_at
    }

    ORDER ||--|{ ORDER_ITEM : contains
    ORDER {
        uuid id PK
        uuid user_id FK
        decimal total_amount
        string status
        datetime created_at
    }

    ORDER_ITEM {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        int quantity
        decimal price
    }
</div>
```

---

## 6. Gantt Charts

### Basic Gantt

```html
<div class="mermaid">
gantt
    title 项目进度
    dateFormat YYYY-MM-DD
    section 设计
    需求分析       :a1, 2025-05-01, 5d
    UI设计         :a2, after a1, 7d
    section 开发
    前端开发       :b1, after a2, 10d
    后端开发       :b2, after a2, 12d
    section 测试
    集成测试       :c1, after b1, 3d
    用户验收       :c2, after c1, 2d
</div>
```

### Gantt with Milestones

```html
<div class="mermaid">
gantt
    title 里程碑计划
    dateFormat YYYY-MM-DD

    section 阶段一
    任务1       :2025-05-01, 7d
    任务2       :2025-05-08, 5d
    里程碑1     :milestone, 2025-05-15, 0d

    section 阶段二
    任务3       :2025-05-16, 10d
    任务4       :2025-05-26, 7d
    里程碑2     :milestone, 2025-06-05, 0d
</div>
```

---

## 7. Pie Charts

```html
<div class="mermaid">
pie title 任务分布
    "开发" : 45
    "测试" : 25
    "文档" : 15
    "会议" : 15
</div>
```

---

## 8. Git Graph

```html
<div class="mermaid">
gitGraph
    commit id: "初始提交"
    branch feature
    checkout feature
    commit id: "功能开发"
    commit id: "功能完善"
    checkout main
    merge feature id: "合并功能"
    branch bugfix
    checkout bugfix
    commit id: "修复bug"
    checkout main
    merge bugfix id: "合并修复"
</div>
```

---

## 9. Mindmap

```html
<div class="mermaid">
mindmap
  root((项目))
    设计
      UI
      UX
      架构
    开发
      前端
        Vue
        React
      后端
        Java
        Python
    测试
      单元测试
      集成测试
      E2E
</div>
```

---

## 10. Timelines

```html
<div class="mermaid">
timeline
    title 项目发展历程
    2025-Q1 : 立项
              需求调研
    2025-Q2 : 开发
              Alpha版本
    2025-Q3 : 测试
              Beta版本
    2025-Q4 : 上线
              持续迭代
</div>
```

---

## Common Patterns

### API Request Flow

```html
<div class="mermaid">
sequenceDiagram
    participant C as 客户端
    participant G as 网关
    participant A as 认证服务
    participant S as 业务服务
    participant D as 数据库

    C->>G: 请求 + Token
    G->>A: 验证Token
    A-->>G: Token有效
    G->>S: 业务请求
    S->>D: 数据操作
    D-->>S: 返回结果
    S-->>G: 业务响应
    G-->>C: API响应
```

### Microservices Architecture

```html
<div class="mermaid">
graph TB
    subgraph 客户端层
        C[Web App]
        M[Mobile App]
    end

    subgraph 网关层
        GW[API Gateway]
    end

    subgraph 服务层
        O[订单服务]
        P[支付服务]
        I[库存服务]
        U[用户服务]
    end

    subgraph 数据层
        DB1[(订单库)]
        DB2[(支付库)]
        DB3[(库存库)]
        DB4[(用户库)]
    end

    C --> GW
    M --> GW
    GW --> O
    GW --> P
    GW --> I
    GW --> U
    O --> DB1
    P --> DB2
    I --> DB3
    U --> DB4
    O -->|同步| P
    P -->|异步| I
</div>
```

### User Journey

```html
<div class="mermaid">
journey
    title 用户购物流程
    section 浏览
      打开APP :5: 用户
      浏览商品 :4: 用户
    section 购买
      加入购物车 :5: 用户
      结算订单 :4: 用户
      选择支付 :3: 用户
    section 完成
      支付成功 :5: 用户
      查看订单 :3: 用户
</div>
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Diagrams not rendering | Ensure mermaid CDN is loaded |
| Dark mode colors | Use `themeVariables` for custom colors |
| Long node text | Use `\n` for line breaks |
| Overlapping elements | Use `spacing` or subgraphs |

### Performance Tips

1. Limit to 20-30 nodes per diagram
2. Use subgraphs to group related elements
3. Prefer simpler diagrams for complex logic (break into multiple)
4. Use `maxTextSize` to prevent oversized labels

---

## Mermaid Resources

- Official Docs: https://mermaid.js.org/syntax/
- Live Editor: https://mermaid.live/
- Cheat Sheet: https://mermaid.js.org/intro/n00b-syntaxReference.html
