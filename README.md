# Universal Skills

统一的 AI Coding Skills 仓库，支持跨工具、跨设备同步。

## 支持的工具

- **Claude Code** - `~/.claude/skills/`
- **Codex** - `~/.codex/skills/`
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
