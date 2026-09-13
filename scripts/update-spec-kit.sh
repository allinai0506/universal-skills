#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# update-spec-kit.sh
#
# 从官方 github/spec-kit 仓库拉取最新模板，自动转换为 categories/imported/ 下的
# SKILL.md 格式，并新增官方新增的命令（如 converge）。
#
# 使用方式：
#   ./scripts/update-spec-kit.sh              # 更新（默认）
#   ./scripts/update-spec-kit.sh --dry-run    # 预览，不实际写入
#   ./scripts/update-spec-kit.sh --no-sync    # 只生成技能，不跑 sync.sh
# =============================================================================

DRY_RUN=false
NO_SYNC=false
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --no-sync) NO_SYNC=true ;;
  esac
done

REPO_DIR="/tmp/spec-kit"
SKILLS_DIR="$(cd "$(dirname "$0")/.." && pwd)/categories/spec-kit"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ----- 1. 获取官方最新代码 -----
echo "==> Fetching official spec-kit repo..."
if [ -d "$REPO_DIR" ]; then
  cd "$REPO_DIR"
  git fetch --depth 1 origin 2>/dev/null || true
  git reset --hard origin/main 2>/dev/null || git reset --hard origin/master 2>/dev/null || true
  # 如果本地还有变更，重新 clean clone
  if ! git diff --quiet; then
    cd /tmp && rm -rf "$REPO_DIR"
    git clone --depth 1 https://github.com/github/spec-kit.git "$REPO_DIR"
  fi
else
  git clone --depth 1 https://github.com/github/spec-kit.git "$REPO_DIR"
fi
cd "$REPO_DIR"
HEAD_SHA=$(git rev-parse --short HEAD)
echo "       HEAD: $HEAD_SHA ($(git log -1 --format='%ad' --date=short))"

# ----- 2. 定义映射关系 -----
#
# 格式: "官方模板路径|技能名|参数提示(可选)|额外source前缀"
# source 前缀自动推断: templates/commands/ -> "templates/commands/"
# git 命令 -> "git:commands/"
# agent-context 命令 -> "agent-context:commands/"
MAPPING=(
  "templates/commands/analyze.md|speckit-analyze||"
  "templates/commands/checklist.md|speckit-checklist|Domain or focus area for the checklist"
  "templates/commands/clarify.md|speckit-clarify|Optional areas to clarify in the spec"
  "templates/commands/constitution.md|speckit-constitution|Principles or values for the project constitution"
  "templates/commands/converge.md|speckit-converge|Optional convergence guidance or task filter"
  "templates/commands/implement.md|speckit-implement|Optional implementation guidance or task filter"
  "templates/commands/plan.md|speckit-plan|Optional guidance for the planning phase"
  "templates/commands/specify.md|speckit-specify|Describe the feature you want to specify"
  "templates/commands/tasks.md|speckit-tasks|Optional task generation constraints"
  "templates/commands/taskstoissues.md|speckit-taskstoissues|Optional filter or label for GitHub issues"
  "extensions/git/commands/speckit.git.commit.md|speckit-git-commit||source-prefix:git:commands/"
  "extensions/git/commands/speckit.git.feature.md|speckit-git-feature||source-prefix:git:commands/"
  "extensions/git/commands/speckit.git.initialize.md|speckit-git-initialize||source-prefix:git:commands/"
  "extensions/git/commands/speckit.git.remote.md|speckit-git-remote||source-prefix:git:commands/"
  "extensions/git/commands/speckit.git.validate.md|speckit-git-validate||source-prefix:git:commands/"
  "extensions/agent-context/commands/speckit.agent-context.update.md|speckit-agent-context-update||source-prefix:agent-context:commands/"
)

# ----- 3. 逐个生成 SKILL.md -----
echo ""
echo "==> Generating SKILL.md files..."

TOTAL=0
UPDATED=0
CREATED=0

for entry in "${MAPPING[@]}"; do
  IFS='|' read -r tpl_path skill_name arg_hint extra <<< "$entry"

  tpl_file="$REPO_DIR/$tpl_path"
  if [ ! -f "$tpl_file" ]; then
    echo "  [SKIP] $tpl_path (not found)"
    continue
  fi

  # 确定 source 值
  if [[ "$extra" == source-prefix:* ]]; then
    prefix="${extra#source-prefix:}"
    source_val="${prefix}${tpl_path#extensions/*/commands/}"
  else
    source_val="$tpl_path"
  fi

  # 解析官方模板 frontmatter + body
  # 用 Python 做 YAML 解析更可靠
  result=$(python3 -c "
import yaml, re, sys

with open('$tpl_file', encoding='utf-8') as f:
    raw = f.read()

# 解析 frontmatter
if raw.startswith('---'):
    parts = raw.split('---', 2)
    if len(parts) >= 3:
        fm = yaml.safe_load(parts[1]) or {}
        body = parts[2]
    else:
        fm = {}
        body = raw
else:
    fm = {}
    body = raw

# 从 frontmatter 提取 description
description = fm.get('description', '')

# 提取 scripts 并解析 {SCRIPT}
scripts = fm.get('scripts', {}) or {}
script_cmd = ''
if isinstance(scripts, dict):
    # 优先选 bash (sh), 其次 py, 最后 ps
    for variant in ('sh', 'py', 'ps'):
        if variant in scripts:
            script_cmd = scripts[variant]
            break

# 替换 {SCRIPT}
if script_cmd:
    body = body.replace('{SCRIPT}', script_cmd)

# 替换 {ARGS} -> \$ARGUMENTS
body = body.replace('{ARGS}', '\$ARGUMENTS')

# 替换 __SPECKIT_COMMAND_X__ -> /speckit-x
def replace_cmd(m):
    name = m.group(1).lower().replace('_', '-')
    return '/speckit-' + name
body = re.sub(r'__SPECKIT_COMMAND_([A-Z][A-Z0-9_]*)__', replace_cmd, body)

# 输出结果（用分隔符避免空格问题）
print('===DESC_START===')
print(description)
print('===DESC_END===')
print('===BODY_START===')
print(body)
print('===BODY_END===')
" 2>&1)

  # 提取 description 和 body
  desc=$(echo "$result" | awk '/===DESC_START===/{flag=1; next} /===DESC_END===/{flag=0} flag' | head -1)
  body=$(echo "$result" | awk '/===BODY_START===/{flag=1; next} /===BODY_END===/{flag=0} flag')

  # 如果 desc 为空，用文件名做默认
  if [ -z "$desc" ]; then
    desc="Spec-kit workflow command: $skill_name"
  fi

  # 构建 frontmatter
  TARGET_DIR="$SKILLS_DIR/$skill_name"
  TARGET_FILE="$TARGET_DIR/SKILL.md"

  # 检查是否已存在
  if [ -f "$TARGET_FILE" ]; then
    EXISTS=true
  else
    EXISTS=false
  fi

  # 构建新内容
  NEW_CONTENT="---
name: \"$skill_name\"
description: \"$desc\""

  if [ -n "$arg_hint" ]; then
    NEW_CONTENT+="
argument-hint: \"$arg_hint\""
  fi

  NEW_CONTENT+="
compatibility: \"Requires spec-kit project structure with .specify/ directory\"
metadata:
  author: \"github-spec-kit\"
  source: \"$source_val\"
user-invocable: true
disable-model-invocation: false
---

$body"

  # 写入或预览
  if [ "$DRY_RUN" = true ]; then
    echo "  [DRY-RUN] $skill_name ($tpl_path)"
    if [ "$EXISTS" = false ]; then
      echo "            -> NEW directory: $TARGET_DIR"
    fi
  else
    mkdir -p "$TARGET_DIR"
    echo "$NEW_CONTENT" > "$TARGET_FILE"
    if [ "$EXISTS" = false ]; then
      echo "  [CREATED] $skill_name"
      CREATED=$((CREATED + 1))
    else
      echo "  [UPDATED] $skill_name"
      UPDATED=$((UPDATED + 1))
    fi
  fi
  TOTAL=$((TOTAL + 1))
done

echo ""
echo "==> Summary: $TOTAL total, $UPDATED updated, $CREATED created"

# 检查是否有被官方移除的技能需要清理
echo ""
echo "==> Checking for removed skills..."
for d in "$SKILLS_DIR"/speckit-*; do
  skill_name=$(basename "$d")
  # 检查是否在 MAPPING 中
  found=false
  for entry in "${MAPPING[@]}"; do
    IFS='|' read -r _ mapped_name _ <<< "$entry"
    if [ "$mapped_name" = "$skill_name" ]; then
      found=true
      break
    fi
  done
  if [ "$found" = false ]; then
    if [ "$DRY_RUN" = true ]; then
      echo "  [DRY-RUN] Would remove obsolete: $d"
    else
      echo "  [REMOVED] $skill_name (no longer in official templates)"
      rm -rf "$d"
    fi
  fi
done

# ----- 4. 同步 -----
if [ "$DRY_RUN" = false ] && [ "$NO_SYNC" = false ]; then
  echo ""
  echo "==> Running sync.sh..."
  cd "$(dirname "$SCRIPT_DIR")"
  bash "$SCRIPT_DIR/../sync.sh"
  echo ""
  echo "==> Done! All speckit skills updated and synced."
elif [ "$DRY_RUN" = true ]; then
  echo ""
  echo "==> Dry-run complete. Run without --dry-run to apply changes."
elif [ "$NO_SYNC" = true ]; then
  echo ""
  echo "==> Skills generated. Run ./sync.sh manually to propagate."
fi