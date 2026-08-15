#!/bin/bash
# 将 universal-skills 中的 superpowers 技能软链接到当前项目的 .trae/skills 目录，
# 以便 TraeCode (IDE) 能够识别它们作为项目级技能。

PROJECT_DIR="/Users/user/universal-skills"
SKILLS_SOURCE_DIR="$PROJECT_DIR/categories"
TARGET_DIR="$PROJECT_DIR/.trae/skills"

mkdir -p "$TARGET_DIR"

# superpowers 技能列表
SKILLS=(
  "brainstorming"
  "deep-dive"
  "deep-interview"
  "dispatching-parallel-agents"
  "executing-plans"
  "finishing-a-development-branch"
  "receiving-code-review"
  "requesting-code-review"
  "root-cause-hunter"
  "subagent-driven-development"
  "systematic-debugging"
  "test-driven-development"
  "using-git-worktrees"
  "using-superpowers"
  "verification-before-completion"
  "writing-plans"
)

echo "=== 正在为 TraeCode 创建项目级技能链接 ==="
for skill in "${SKILLS[@]}"; do
  dest=$(find "$SKILLS_SOURCE_DIR" -maxdepth 3 -type d -name "$skill" | head -1)
  if [ -d "$dest" ]; then
    link="$TARGET_DIR/$skill"
    if [ -L "$link" ]; then
      rm -f "$link"
    fi
    ln -sf "$dest" "$link"
    echo "Linked $skill -> $dest"
  else
    echo "Warning: Could not find directory for $skill"
  fi
done

echo "=== 项目级 Skills 目录已创建 ==="
ls -la "$TARGET_DIR"
