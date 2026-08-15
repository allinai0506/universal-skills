#!/bin/bash
# 彻底修复所有 Trae 技能目录下的 symlink 问题
# 将所有 symlink 技能替换为真实副本

SKILLS_SOURCE_DIR="/Users/user/universal-skills/categories"

# 需要修复的目录
DIRS=(
  "$HOME/.trae/skills"
  "$HOME/.trae-cn/skills"
  "$HOME/.codex/skills"
)

echo "=== 正在彻底修复 Trae 技能加载问题 ==="

for TARGET_DIR in "${DIRS[@]}"; do
  if [ ! -d "$TARGET_DIR" ]; then
    echo "跳过不存在的目录: $TARGET_DIR"
    continue
  fi
  
  echo ""
  echo "--- 处理目录: $TARGET_DIR ---"
  
  # 遍历目录下的所有 symlink
  for link in "$TARGET_DIR"/*; do
    if [ -L "$link" ]; then
      link_name=$(basename "$link")
      dest=$(readlink "$link")
      
      # 检查 symlink 指向的源是否存在
      if [ -d "$dest" ]; then
        echo "修复 symlink: $link_name"
        rm -f "$link"
        cp -R "$dest" "$link"
      else
        echo "警告: symlink $link_name 指向的源不存在 ($dest)，跳过"
      fi
    fi
  done
done

echo ""
echo "=== 修复完成！请重启 Trae 所有窗口 ==="
