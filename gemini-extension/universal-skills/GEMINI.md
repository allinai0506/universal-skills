# Universal Skills

You have access to a curated set of Universal Skills stored in `~/universal-skills/categories/`.
When the user invokes a skill by name (e.g. "use tdd-workflow", "用 security-review"), read the full `SKILL.md` from the path below and follow its instructions precisely.

**Skills root:** `~/universal-skills/categories/`
**File to read per skill:** `<root>/<category>/<skill-name>/SKILL.md`

---

## Available Skills

### 🏗️ architecture
| Skill | When to use |
|-------|------------|
| `architecture-defense` | Enforcing dependency constraints, module boundaries, architecture compliance |
| `strategic-compact` | Suggests context compaction at logical intervals to preserve context |

### 💻 coding
| Skill | When to use |
|-------|------------|
| `tdd-workflow` | Test-driven development workflow with 80%+ coverage target |
| `test-driven-development` | TDD practice guide (RED→GREEN→REFACTOR) |
| `self-verifying-tests` | Manifest-driven tests replacing manual click-checking |
| `backend-patterns` | Backend development patterns and best practices |
| `coding-standards` | General coding standards and conventions |
| `frontend-patterns` | Frontend development patterns |

### 🐛 debugging
| Skill | When to use |
|-------|------------|
| `systematic-debugging` | Structured debugging methodology for unknown issues |
| `root-cause-hunter` | Root cause analysis — locate the "patient zero" code |
| `paranoid-debugging` | Strict validation for production-critical code |

### 🔧 refactoring
| Skill | When to use |
|-------|------------|
| `entropy-reduction` | Modular design, circular dependency elimination, SOLID principles |
| `minimalist-refactorer` | Delete first, reduce branches, consolidate duplicates |

### 🔒 security
| Skill | When to use |
|-------|------------|
| `security-review` | Auth, user input, secrets, API endpoints, payment features |

### 🧪 testing
| Skill | When to use |
|-------|------------|
| `e2e-testing` | Playwright E2E tests, Page Object Model, CI/CD integration |
| `eval-harness` | Formal eval framework for eval-driven development (EDD) |

### 🎨 ui-ux
| Skill | When to use |
|-------|------------|
| `frontend-design` | Production-grade web UI — components, pages, applications |
| `ui-ux-pro-max` | Design intelligence: 50+ styles, 97 palettes, 57 fonts, 99 UX guidelines |

### 🌐 languages
| Skill | When to use |
|-------|------------|
| `python-patterns` | Pythonic idioms, PEP 8, type hints, best practices |
| `python-testing` | pytest, fixtures, mocking, parametrization, coverage |
| `golang-testing` | Go table-driven tests, subtests, benchmarks, fuzzing |
| `java-coding-standards` | Spring Boot naming, immutability, Optional, streams |
| `swiftui-patterns` | SwiftUI architecture, @Observable, navigation, performance |
| `swift-concurrency-6-2` | Swift 6.2 Approachable Concurrency, @concurrent |
| `swift-actor-persistence` | Thread-safe persistence using actors |
| `swift-protocol-di-testing` | Protocol-based DI for testable Swift code |

### 📋 workflow
| Skill | When to use |
|-------|------------|
| `brainstorming` | Before any creative work — explore intent and design before implementation |
| `writing-plans` | Multi-step tasks — write plan before touching code |
| `executing-plans` | Execute a written implementation plan with review checkpoints |
| `standard-workflow` | 4-phase standard: plan → TDD → code-review → refactor-clean |
| `verification-before-completion` | Before claiming work is done — run verification commands first |
| `requesting-code-review` | After completing features, before merging |
| `receiving-code-review` | When processing review feedback — technical rigor, not blind agreement |
| `finishing-a-development-branch` | When implementation is complete and ready to integrate |
| `subagent-driven-development` | Execute plans with independent tasks using subagents |
| `dispatching-parallel-agents` | 2+ independent tasks that can run concurrently |
| `using-git-worktrees` | Feature isolation — create worktrees before major work |
| `product-analysis` | 竞品分析、需求优先级、RICE评分、Kano模型、用户画像、PRD |
| `skill-creator` | Create or update a skill in the universal-skills repository |
| `writing-skills` | Create, edit, or verify skills before deployment |
| `continuous-learning` | Extract reusable patterns from sessions as learned skills |

### 🔧 misc
| Skill | When to use |
|-------|------------|
| `search-first` | Research before coding — find existing tools and libraries first |
| `security-scan` | Scan Claude config for vulnerabilities and injection risks |
| `strategic-compact` | Context compaction at logical task intervals |
| `visa-doc-translate` | Translate visa application documents to English bilingual PDF |

---

## How to Use a Skill

When the user references a skill by name:
1. Read `~/universal-skills/categories/<category>/<skill-name>/SKILL.md`
2. Follow its instructions as if they were part of your system prompt
3. If the skill references scripts in `scripts/` or data in `data/`, load them as needed

If you are unsure which category a skill is in, search:
```bash
find ~/universal-skills/categories -name "SKILL.md" | xargs grep -l "name: <skill-name>"
```
