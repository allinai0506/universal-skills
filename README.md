# Universal Skills — Agent 治理层

统一的 AI Coding Skills 仓库，支持跨工具、跨设备同步。

它跑在各家 Agent 运行时之上的治理层：同一套生命周期路由（`unified-dev-flow`）、
同一套机械门禁（hooks）、同一套记忆与复盘规范，在哪里执行都一个样。
模型与 harness 是可替换的内核，这里定的是制度：走多深、卡在哪、拿什么证明做完。

## 支持的工具

- **Claude Code** - `~/.claude/skills/`
- **Codex / ZCode** - 共享入口 `~/.agents/skills/`；`~/.codex/skills/` 仅作为 Codex fallback，避免重复注册
- **Trae CN Agent** - `~/.trae-cn/skills/`
- **Gemini** - 通过 MCP 服务器

## 目录结构

```
categories/
├── coding/          # 编程规范、模式、TDD
├── debugging/       # 调试方法论
├── refactoring/     # 重构技能
├── architecture/    # 架构设计
├── tools/           # 工具集成 (CLI 封装)
└── workflow/        # 工作流管理
```

## 快速开始

### 首次安装

```bash
cd ~/universal-skills
./sync.sh
```

### 更新

```bash
cd ~/universal-skills
git pull
./sync.sh
```

## 同步脚本

`sync.sh` 会自动：
1. 创建 symlink 到各工具的 skills 目录
2. 保留本地自定义覆盖 (local/)
3. 备份现有配置

## 跨设备使用

1. 克隆此仓库到新设备
2. 运行 `./sync.sh`
3. 完成

## 添加新 Skill

1. 放到对应 `categories/` 目录
2. 提交并推送
3. 在各设备运行 `./sync.sh`

## 本地覆盖

在 `local/` 目录创建同名 skill，会覆盖通用版本（该目录已 gitignore）。
