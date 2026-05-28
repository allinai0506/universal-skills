#!/usr/bin/env bash
# =============================================================================
# install-hooks.sh — 安装 Git hooks 到 .git/hooks/
# 用法: ./install-hooks.sh
# =============================================================================

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_SRC="$REPO_DIR/hooks"
HOOKS_DST="$REPO_DIR/.git/hooks"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

if [ ! -d "$HOOKS_SRC" ]; then
    echo "❌ hooks/ 目录不存在，请先确认仓库结构"
    exit 1
fi

echo "📦 安装 Git Hooks..."
echo ""

for hook_file in "$HOOKS_SRC"/*; do
    hook_name="$(basename "$hook_file")"
    target="$HOOKS_DST/$hook_name"

    # 备份已有 hook
    if [ -f "$target" ] && [ ! -L "$target" ]; then
        echo -e "${YELLOW}  ⚠️  已有 $hook_name，备份为 $hook_name.bak${RESET}"
        mv "$target" "$target.bak"
    fi

    # 建立软链接（这样 hook 本身可以被 git 追踪）
    ln -sf "$hook_file" "$target"
    chmod +x "$hook_file"
    echo -e "${GREEN}  ✅ $hook_name → .git/hooks/$hook_name${RESET}"
done

echo ""
echo -e "${GREEN}✨ Hooks 安装完成！${RESET}"
echo ""
echo "现在每次 commit 涉及技能文件时，将自动："
echo "  1. 同步到所有本地 Agents（Claude/Cursor/Codex/Gemini）"
echo "  2. Push 到 GitHub"
