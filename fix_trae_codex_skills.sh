#!/bin/bash
# 修复 TraeCode (Codex) 无法加载 symlink 技能的问题
# 将 superpowers 技能从 universal-skills 真实复制到 ~/.codex/skills

SKILLS_SOURCE_DIR="/Users/user/universal-skills/categories"
TARGET_DIR="$HOME/.codex/skills"

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

echo "=== 正在修复 TraeCode 技能加载问题 (替换 symlink 为真实副本) ==="
echo "目标目录: $TARGET_DIR"
echo ""

for skill in "${SKILLS[@]}"; do
  dest=$(find "$SKILLS_SOURCE_DIR" -maxdepth 3 -type d -name "$skill" | head -1)
  if [ -d "$dest" ]; then
    target_path="$TARGET_DIR/$skill"
    
    # 如果存在 symlink，先删除
    if [ -L "$target_path" ]; then
      rm -f "$target_path"
      echo "Removed symlink: $skill"
    elif [ -d "$target_path" ]; then
      # 如果是真实目录，为了保险也删除重建（确保是最新的）
      rm -rf "$target_path"
      echo "Removed existing dir: $skill"
    fi
    
    # 真实复制
    cp -R "$dest" "$target_path"
    echo "Copied $skill (real directory now)"
  else
    echo "Warning: Could not find source for $skill"
  fi
done

echo ""
echo "=== 修复完成！检查结果 ==="
echo "请重启 TraeCode 以使新技能生效。"
echo ""
ls -la "$TARGET_DIR" | grep -E "lrwxr|drwxr" | head -20 # 显示前20个，确认没有lrwxr (symlink)
