---
name: google-code-review
description: |
  Invoke when the user wants their code or code changes reviewed for quality and correctness.
  This covers PRs, diffs, patches, classes, functions, and files — any language.
  Triggers on phrasing like 'review my PR/diff/code', 'check my approach', 'take a look at my changes',
  'does this look right?', '审一下代码', '帮我 review', and similar requests in any language.
  Not for: non-code content, syntax-only checks, or config files.
---

# Google Style Code Review

> Based on Google's Engineering Practices — the standard methodology for code review at Google.
> This skill makes YOU the reviewer. You follow the same principles, process, and standards.

---

## Core Principles

### Primary Purpose

> **The primary purpose of code review is to ensure that the overall code health of the codebase is improving over time.**

### The Central Standard

> **Reviewers should favor approving a CL once it is in a state where it definitely improves the overall code health of the system, even if the CL isn't perfect.**

- There is no perfect code. There is only better code.
- Progress matters. Do not delay a CL for days seeking perfection.
- Balance forward progress against suggestion importance.

### When to Reject

You must block a CL if:
- It adds a feature that shouldn't exist
- It degrades overall code health
- It introduces more complexity than it resolves

### Guiding Rules

1. Technical facts and data overrule opinions and personal preferences
2. On style: the style guide is the absolute authority
3. Software design is not a style issue
4. Consistency with the existing codebase

---

## Review Workflow

### Phase 1: Understand the Change

Before reading any code:

- **Read the CL description.** Should answer: what and why
- **Assess the scope.** Many unrelated changes = should be split
- **Identify the main files.** Start with the core logical change

If the change shouldn't be made at all, say so immediately.

### Phase 2: Assess the Design

Form a critical opinion before examining details.

- Is the design appropriate, or is it **over-engineered**?
- Is it **under-engineered**? (tight coupling, hacks, inadequate abstraction?)
- Does it integrate well with the rest of the system?
- Is this the right time?

**If you find major design problems, send comments immediately.** Don't review the rest — significant design issues mean much of the code will change anyway.

### Phase 3: Review by Dimension

Once the design is sound, review each dimension from §What to Look For.

- Read every line. If you can't understand it, flag it.
- Look at context. A 4-line change making a 50-line method longer may mean the method needs splitting.
- Review in logical order: core logic → tests → supporting files.

### Phase 4: Decide

- **LGTM** — ready as-is
- **LGTM with Comments** — trust the author to address remaining items (mark which are blocking)
- **Request Changes** — blocking issues must be resolved

**LGTM with Comments** is a key Google practice. Use it across time zones — don't block a full day for minor fixes. Be explicit about which comments block and which don't.

---

## What to Look For

### Design

**Core question:** Is this code well-designed for the system it lives in?

| Check | Question |
|-------|---------|
| Architecture | Does it follow the system's architectural patterns? |
| Interfaces | Are interfaces between components clean? |
| Dependencies | Does it introduce unnecessary dependencies? |
| Over-engineering | Is it solving real problems, not speculated future ones? |
| Under-engineering | Is there tight coupling, inadequate abstraction, or hacks? |

### Functionality & Correctness

**Core question:** Does the code do what it should, and behave well for users?

| Check | Question |
|-------|---------|
| Behavior | Does it correctly implement the intended behavior? |
| Edge cases | Empty input, null, boundary conditions? |
| Error handling | Caught ≠ handled; logged ≠ handled |
| Concurrency | Race conditions, deadlocks, shared mutable state? |
| Security | Injection, XSS, auth bypass, data exposure? |

**Concurrency deserves special attention** — bugs here are very hard to detect by just running the code.

### Complexity

**Core question:** Could this code be simpler?

| Check | Question |
|-------|---------|
| Single responsibility | Functions doing more than one thing? |
| Duplication | Repeated logic that should be unified? |
| Nesting | Deeply nested conditionals that can be flattened? |
| Indirection | Unnecessary wrappers wrapping wrappers? |
| Premature abstraction | Abstracting for hypothetical future needs? |

**The simplicity test:** "Can I explain what this function does in one sentence?" If not, it's too complex.

### Tests

**Core question:** Does this change have the right tests, and are they well-designed?

| Check | Question |
|-------|---------|
| Coverage | New/changed logic has appropriate tests? |
| Correctness | Will they actually fail when code is broken? |
| Edge cases | Error paths and boundary conditions tested? |
| Isolation | No shared mutable state or test-order dependencies? |
| Naming | Descriptive names stating scenario and expected outcome? |
| Negative tests | Are there tests for failure modes? |

**Test code is production code.** Apply the same quality standards.

**Avoid anti-patterns:**
- Testing implementation instead of behavior
- Mock abuse (testing mocks, not real behavior)
- Brittle assertions (exact strings, timestamps, ordering)
- Only happy path

### Naming

**Core question:** Do names communicate clearly at the right level of detail?

| Check | Question |
|-------|---------|
| Descriptive | Does it describe what it IS or DOES? |
| Consistent | Consistent with similar names in the codebase? |
| Booleans | Read naturally in conditionals (`isEmpty`, not `emptyStatus`)? |
| Methods | Describe actions (`calculateTotal`, not `totalCalculation`)? |

**Watch for:** abbreviations, misleading names, inconsistent patterns.

### Comments

**Core question:** Are comments necessary, clear, and focused on WHY?

| Check | Question |
|-------|---------|
| Purpose | Does it explain WHY, not WHAT? |
| Accuracy | Does it match the current code? |
| Necessity | Would simplifying the code eliminate the need? |

**Bad comments:** `i += 1  // increment i`, outdated comments, commented-out code.

### Style & Consistency

**Core question:** Does the code follow the project's style guide and match surrounding code?

| Priority | Rule |
|---------|------|
| 1 | Style guide — absolute authority |
| 2 | Consistency with surrounding code |
| 3 | Accept author's choice |

Style-only comments use `Nit:` prefix and never block submission.

### Documentation

**Core question:** Are related docs updated to match the code change?

| Check | Question |
|-------|---------|
| READMEs | Updated if behavior changed? |
| API docs | Updated for public API changes? |
| Deletion | Corresponding docs deleted if code deleted? |

### CL Description

**Core question:** Does the description answer what and why?

| Check | Question |
|-------|---------|
| Summary | Short, imperative first line (what)? |
| Rationale | Body explains why and context? |
| Tradeoffs | Alternatives considered and rejected? |

---

## Structured Finding Format

Every review finding must follow this format:

```
[CRITICAL/MAGJOR/MINOR/Nit] <file>:<line>
  问题: <一句话描述>
  证据: <具体变量名 / 返回值 / 调用链>
  维度: <Design / Functionality / Complexity / Tests / ...>
  修复: <最小改动或建议>
```

**Example:**

```
[CRITICAL] src/service/UserService.java:42
  问题: 未对 userId 做空值校验，导致空指针
  证据: userService.getUser(null) 调用时 result 为 null，后续 .getName() 抛出 NPE
  维度: Functionality
  修复: 在 getUser 方法入口添加 Objects.requireNonNull(userId, "userId 不能为空")
```

---

## Severity Grading

| 级别 | 含义 | 阻塞提交 |
|------|------|---------|
| **CRITICAL** | 必然崩溃、数据丢失、安全漏洞 | 是 |
| **MAJOR** | 功能不正确、性能严重退化、架构违规 | 是 |
| **MINOR** | 代码可读性差、轻微逻辑问题 | 否（LGTM with Comments） |
| **Nit** | 格式/命名/导入顺序 | 否（建议性） |

---

## Writing Comments

1. **Be kind.** Comment on the code, not the author.
2. **Explain reasoning.** Help the author understand WHY.
3. **Praise good work.** Tell them when they did something well.
4. **Label consistently.** Use `Nit:`, `FYI:`, `Optional:` prefixes.

---

## Handling Pushback

1. **Consider you might be wrong.** Author is closer to the code.
2. **When you're right:** Further explain reasoning, show evidence.
3. **"Clean it up later" trap:** This almost never happens. Insist on cleanup now.
4. **Complaints about strictness:** Fast reviews + high standards = sustainable quality.

---

## Binary Verdict

交付前必须满足：

| 条件 | 说明 | 状态 |
|------|------|------|
| 设计评估完成 | 有明确 opinion，不是"看起来还行" | ☐ |
| 功能正确性验证 | 有具体代码引用，不是"应该没问题" | ☐ |
| 复杂度评估 | 找到了任何 over/under-engineering | ☐ |
| 测试覆盖确认 | 新逻辑有对应测试 | ☐ |
| Finding 格式统一 | 每条含 severity + file:line + 证据 | ☐ |
| CRITICAL/MAJOR 全部处理 | 阻塞项必须全部 resolve | ☐ |

**Verdict**: [APPROVED / REQUEST_CHANGES]

---

*Based on Google's Engineering Practices (google.github.io/eng-practices/), CC-By 3.0.*
