# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

Universal Skills is a unified AI coding skills repository that synchronizes across multiple AI development tools:
- **Codex** (`~/.Codex/skills/`)
- **Codex / ZCode shared user skills** (`~/.agents/skills/`; Codex's `~/.codex/skills/` is fallback-only)
- **Trae CN Agent** (`~/.trae-cn/skills/`)
- **Gemini CLI** (via MCP extension and project symlinks)

Skills are modular, self-contained folders that extend AI capabilities with specialized knowledge, workflows, and tool integrations.

## Commands

### Sync Skills to All Tools
```bash
./sync.sh
```

This script:
1. Symlinks skills from `categories/` to each project's `.Codex/skills/`（零磁盘开销）
2. Discovers project-unique hidden skills and imports them to `categories/imported/`
3. Creates symlinks in configured projects (`clawd`, `xiyu`, etc.)
4. Manages Gemini extension and MCP configuration
5. Auto-cleans old backups（保留最新 2 份）

**Run after:** Adding new skills, modifying existing skills, or pulling updates.

### Discover Hidden Skills in Projects
```bash
./sync.sh --discover
```
Scans all known projects for skills not yet in `categories/` and imports them to `categories/imported/`. Run this periodically or when starting work in a new project.

### Test a Skill's Search Function (ui-ux-pro-max)
```bash
python3 categories/ui-ux/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain>
python3 categories/ui-ux/ui-ux-pro-max/scripts/search.py "<query>" --design-system [-p "Project Name"]
```

### Initialize a New Skill
```bash
python3 categories/.system/skill-creator/scripts/init_skill.py <skill-name>
```

## Directory Structure

```
categories/
├── .system/              # Meta-tools (skill-creator)
├── architecture/         # Architecture patterns (access-pattern-driven-data-modeling, cog-4d-audit)
├── coding/              # Development patterns (TDD, API design, performance)
├── debugging/           # Debugging methodologies (systematic, root-cause, paranoid)
├── deployment/          # Deployment & migrations (database-migrations, xiyu-server-deploy)
├── engineering/         # Engineering workflows (code-review, domain-modeling, prototype)
├── gstack/              # gstack bundle (browse, health, plan-eng-review, ship, canary)
├── imported/            # Auto-discovered skills from projects (gitignored)
├── misc/                # Misc (strategic-compact)
├── pstack/              # pstack bundle (architect, interrogate, swarm, technical-writing)
├── refactoring/         # Refactoring practices (entropy reduction, ai-slop-cleaner)
├── security/              # Security review checklist
├── spec-kit/            # Spec Kit commands (speckit-*)
├── testing/             # Testing (e2e-testing)
├── ui-ux/              # Frontend design (frontend-design, ui-ux-pro-max, motion-design)
└── workflow/           # Development workflows (unified-dev-flow, brainstorming, writing-plans)

local/                  # Local overrides (gitignored)
.backup/                # Timestamped backups (auto-cleaned, gitignored)
```

## Skill Anatomy

Every skill follows this structure:

```
skill-name/
├── SKILL.md                    # Required: Frontmatter + instructions
│   ├── YAML frontmatter        # name, description (triggers)
│   └── Markdown body           # Instructions loaded after trigger
├── skill-metadata.yml          # Optional: Platform compatibility, triggers
├── agents/
│   └── openai.yaml            # Recommended: UI metadata for skill lists
├── scripts/                    # Optional: Executable code (Python/Bash)
├── references/                 # Optional: Documentation to load as needed
└── data/                       # Optional: Data files (CSV, JSON, etc.)
```

### SKILL.md Frontmatter (Required)

```yaml
---
name: skill-name
description: Use when [clear trigger conditions]. Describe what the skill does.
---
```

**Critical:** The `description` field determines when AI tools invoke the skill. Be explicit about trigger conditions.

### Optional Resources

- **`scripts/`** - Executable code for tasks requiring deterministic reliability or repeated rewriting
- **`references/`** - Documentation loaded into context as needed
- **`data/`** - Structured data files (CSV, JSON) for skill operations
- **`skill-metadata.yml`** - Platform compatibility, tool dependencies, trigger keywords

## Skill Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| `architecture/` | System design, constraints | access-pattern-driven-data-modeling |
| `coding/` | Development patterns | test-driven-development, self-verifying-tests |
| `debugging/` | Debugging methodologies | systematic-debugging, root-cause-hunter |
| `refactoring/` | Code cleanup | entropy-reduction |
| `ui-ux/` | Frontend design | ui-ux-pro-max, frontend-design |
| `workflow/` | Process management | brainstorming, writing-plans, skill-creator |

## Local Overrides

The `local/` directory allows per-machine skill customization:

1. Create `local/<skill-name>/SKILL.md`
2. It will override the version in `categories/`
3. `local/` is gitignored

## Key Architectural Patterns

### ui-ux-pro-max

Contains Python-based search engine with BM25 ranking:
- **Data files:** `styles.csv`, `colors.csv`, `typography.csv`, `ux-guidelines.csv`
- **Scripts:** `search.py`, `design_system.py`, `core.py`
- **Usage:** Search across 50+ styles, 97 palettes, 57 fonts, 99 UX guidelines

### self-verifying-tests

Manifest-driven test generation with cross-layer validation:
- **Generators:** `manifest-scanner.ts`, `playwright-generator.ts`
- **Validators:** `shadow-inspector.ts`, `doc-integrity.ts`
- **Four layers:** Manifest-driven, Shadow Inspector (UI/DB), FSM state testing, Doc-code integrity

### skill-creator

Meta-tool for creating new skills with:
- `init_skill.py` - Scaffold new skill structure
- `generate_openai_yaml.py` - Generate agents/openai.yaml metadata
- `quick_validate.py` - Validate skill structure

## Adding New Skills

1. Create skill directory in appropriate `categories/` subdirectory
2. Add `SKILL.md` with clear frontmatter (`name`, `description`)
3. (Optional) Add `skill-metadata.yml` for platform compatibility
4. (Optional) Create `agents/openai.yaml` for UI metadata
5. Run `./sync.sh` to propagate to all tools
6. Commit and push

## Sync Script Details

The `sync.sh` script handles:
- **Codex 项目级:** Symlink 所有技能到每个项目的 `.Codex/skills/`（零磁盘开销）
- **Codex / ZCode:** 以 `~/.agents/skills/` 作为共享技能入口；`~/.codex/skills/` 只补充共享入口缺失项并保留 `.system`，避免同名技能双重注册
- **Trae CN Agent:** 增量 symlink 到 `~/.trae-cn/skills/`，保护 marketplace/builtin 技能
- **ZCode/Agent:** 增量 symlink 到 `~/.agents/skills/`，清理旧 `~/.zcode/skills/` universal symlink 避免重复加载
- **Cursor:** 不再生成 `.cursor/rules/*.mdc` 技能规则
- **Project symlinks:** 在 xiyu worktrees 等项目下创建 `skills/universal-skills` symlink
- **技能发现:** 自动扫描项目中的独有技能，import 到 `categories/imported/`
- **备份:** 自动备份并在下次备份时清理旧版本（保留 2 份）
- **Backups:** 自动备份 `target` 目录，然后在下次备份时清理旧版本

### 清除垃圾文件

```bash
# 手动清理备份（保留最新 2 份，sync.sh 运行时会自动完成）
ls -1t .backup/ | tail -n +3 | while read old; do rm -rf ".backup/$old"; done

# 删除旧的已跟踪备份（如果曾提交过）
git rm -r .backup/skills-*
```

### 技能发现

```bash
# 扫描所有项目，发现不在 categories/ 中的独有技能
./sync.sh --discover

# 手动列出项目中的技能
find ~/xiyu ~/clawd -maxdepth 4 -name "SKILL.md" -path "*/.Codex/skills/*" 2>/dev/null
```

## File Naming Conventions

- Skills: `kebab-case` directory names
- SKILL.md: Always exactly `SKILL.md` (uppercase)
- Scripts: `snake_case.py` for Python
- Data files: `kebab-case.csv` for structured data

## 开发流程断点恢复

开发任务开始前，必须先检查当前 worktree 是否存在未完成的开发流程状态：

1. 检查 `.superpowers/sdd/` 目录下是否有 ledger 文件（`progress.md`）
2. 若存在，读取 ledger 首行确认所属计划文件，再按 `Task <N>: complete` 行确定断点位置
只有在确认没有未完成的 ledger 或计划文件后，才走 unified-dev-flow 的正常分级路由。

## 统一开发流程硬门禁铁律 (Unified Dev Flow Gates)

在任何项目推进开发时，必须严格遵守统一开发流程（unified-dev-flow）的阶段门禁，绝不允许跨步冲刺：

1. **S4 退出清理门禁 (Mandatory Mode B)**：源码修改完成后，必须先执行 `ai-slop-cleaner` 模式 B（deletion-first 瘦身/删死代码/化简层级），严禁直接带着 slop 代码进入 S5。
2. **S5 验证证据门禁**：必须针对瘦身后的代码运行验证命令，并将命令退出码和证据写入 `.omc/verify-<session>.md`。
3. **S6 Code Review 物理硬前置**：
   - **S6 是 S7 Deliver（提 PR / git push / 分支收尾）的不可逆硬前置**！
   - 严禁在未生成 `.omc/review-<session>.md` 且 `verdict: MERGE_READY` 之前执行任何 `git push`、创建 PR 或收尾任务！
   - **系统已在物理层面设卡拦截**：
     - `git push` 会触发 Git `pre-push` 门禁，无合格评审工件直接阻断（exit 1）；
     - PR 创建脚本（如 `gitee-pr-helper.sh create`）会自动执行 `--guard-pr`，不达标直接拒绝建 PR；
     - 任务收尾脚本（如 `agent-finish-task.sh` / `finish-task.sh`）会强制复核 S6 审查工件；
     - AI 宿主 Stop Hook（`--check-review`）会在会话结束前强制核验。
   - 必须通过独立审视者（`xiyu-code-review` / `google-code-review`），取得 `MERGE_READY` 后，方可进入 S7 交付。

