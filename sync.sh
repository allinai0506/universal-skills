#!/bin/bash
# Universal Skills 同步脚本 v2
# 将 ~/universal-skills 同步到各 AI Coding 工具

set -e

UNIVERSAL_SKILLS="$HOME/universal-skills"
BACKUP_DIR="$UNIVERSAL_SKILLS/.backup"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }
info() { echo -e "${CYAN}→${NC} $1"; }

# 创建备份
backup() {
    local dir="$1"
    if [ -d "$dir" ] && [ ! -L "$dir" ]; then
        mkdir -p "$BACKUP_DIR"
        local backup_name="$(basename "$dir")-$(date +%Y%m%d-%H%M%S)"
        log "备份 $dir 到 $BACKUP_DIR/$backup_name"
        cp -R "$dir" "$BACKUP_DIR/$backup_name"
    fi
}

# 同步到全局 Claude（保留，用于某些情况）
sync_claude_global() {
    local target="$HOME/.claude/skills"

    if [ -d "$target" ] && [ ! -L "$target" ]; then
        backup "$target"
        rm -rf "$target"
    fi

    mkdir -p "$target"
    cp -r "$UNIVERSAL_SKILLS/categories"/* "$target/"

    success "Claude Code 全局 skills 已同步 (~/.claude/skills/)"
    warn "  注意: Claude Code 主要加载项目级 skills，全局目录仅供参考"
}

# 同步到项目级 Claude（这才是真正有用的）
sync_claude_projects() {
    local synced_count=0
    local skill_count_total=0

    # 自动发现所有包含 .claude 目录的项目
    local found_projects=()

    # 搜索用户目录下的项目
    while IFS= read -r -d '' project_dir; do
        # 跳过 universal-skills 自身和隐藏目录
        if [[ "$project_dir" == *"universal-skills"* ]] || [[ "$project_dir" == *"/."* ]]; then
            continue
        fi
        # 检查是否有 .claude 目录
        if [ -d "$project_dir/.claude" ]; then
            found_projects+=("$project_dir")
        fi
    done < <(find "$HOME" -maxdepth 2 -type d -print0 2>/dev/null)

    # 也搜索常见项目目录
    for base_dir in "$HOME/code" "$HOME/projects" "$HOME/work" "$HOME/Documents"; do
        if [ -d "$base_dir" ]; then
            while IFS= read -r -d '' project_dir; do
                if [ -d "$project_dir/.claude" ]; then
                    found_projects+=("$project_dir")
                fi
            done < <(find "$base_dir" -maxdepth 1 -type d -print0 2>/dev/null)
        fi
    done

    # 去重
    local unique_projects=($(printf "%s\n" "${found_projects[@]}" | sort -u))

    log "发现 ${#unique_projects[@]} 个包含 .claude 的项目"

    for project_dir in "${unique_projects[@]}"; do
        local project_name="$(basename "$project_dir")"
        local skills_dir="$project_dir/.claude/skills"

        # 创建 skills 目录
        mkdir -p "$skills_dir"

        # 同步技能
        local skill_count=0
        for category_dir in "$UNIVERSAL_SKILLS/categories"/*; do
            if [ -d "$category_dir" ]; then
                local category_name="$(basename "$category_dir")"
                # 复制整个分类目录
                cp -rn "$category_dir" "$skills_dir/" 2>/dev/null || true
                # 统计技能数
                while IFS= read -r skill_md; do
                    ((skill_count++))
                done < <(find "$category_dir" -name "SKILL.md" 2>/dev/null)
            fi
        done

        if [ $skill_count -gt 0 ]; then
            log "  → $project_name: $skill_count 个技能"
            synced_count=$((synced_count + 1))
            skill_count_total=$((skill_count_total + skill_count))
        fi
    done

    if [ $synced_count -gt 0 ]; then
        success "已同步 $synced_count 个项目的 skills ($skill_count_total 个技能文件)"
    else
        warn "未找到任何项目"
    fi
}

# 同步到 Codex
sync_codex() {
    local target="$HOME/.codex/skills"

    if [ ! -d "$HOME/.codex" ]; then
        return
    fi

    if [ -d "$target" ] && [ ! -L "$target" ]; then
        backup "$target"
    fi

    rm -rf "$target"
    mkdir -p "$target"

    local skill_count=0

    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
            local skill_name="$(basename "$skill_dir")"
            cp -r "$skill_dir" "$target/$skill_name"
            skill_count=$((skill_count + 1))
        fi
    done

    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*; do
        if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
            local skill_name="$(basename "$skill_dir")"
            if [ ! -d "$target/$skill_name" ]; then
                cp -r "$skill_dir" "$target/$skill_name"
                skill_count=$((skill_count + 1))
            fi
        fi
    done

    success "Codex skills 已同步 ($skill_count 个技能)"
}

# 同步到 Gemini
sync_gemini() {
    if ! command -v gemini &> /dev/null; then
        return
    fi

    local extension_dir="$UNIVERSAL_SKILLS/gemini-extension/universal-skills"

    if [ ! -f "$extension_dir/gemini-extension.json" ]; then
        return
    fi

    if gemini extensions list 2>/dev/null | grep -q "universal-skills"; then
        log "Gemini extension 已安装"
    else
        log "安装 Gemini extension..."
        echo "Y" | gemini extensions link "$extension_dir" > /dev/null 2>&1 || true
    fi

    success "Gemini extension 已就绪"
}

# 创建本地覆盖目录
mkdir -p "$UNIVERSAL_SKILLS/local"

# 解析命令行参数
SKIP_GLOBAL=false
SKIP_PROJECTS=false
SKIP_CODEX=false
SKIP_GEMINI=false
SPECIFIC_PROJECT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-global) SKIP_GLOBAL=true ;;
        --no-projects) SKIP_PROJECTS=true ;;
        --no-codex) SKIP_CODEX=true ;;
        --no-gemini) SKIP_GEMINI=true ;;
        --project=*) SPECIFIC_PROJECT="$2"; shift ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --no-global     跳过全局 Claude 同步"
            echo "  --no-projects   跳过项目级同步"
            echo "  --no-codex      跳过 Codex 同步"
            echo "  --no-gemini     跳过 Gemini 同步"
            echo "  --project NAME  只同步指定项目"
            echo "  --help          显示此帮助"
            exit 0
            ;;
        *) shift ;;
    esac
    shift
done

log "开始同步 Universal Skills..."
echo ""

if [ "$SKIP_GLOBAL" = false ]; then
    sync_claude_global
    echo ""
fi

if [ "$SKIP_PROJECTS" = false ]; then
    sync_claude_projects
    echo ""
fi

if [ "$SKIP_CODEX" = false ]; then
    sync_codex
    echo ""
fi

if [ "$SKIP_GEMINI" = false ]; then
    sync_gemini
    echo ""
fi

success "同步完成！"
echo ""
echo "提示："
echo "  - 本地自定义技能: $UNIVERSAL_SKILLS/local/"
echo "  - 备份位置: $BACKUP_DIR"
echo "  - ⚠️  重启 Claude Code 以加载新 skills"
echo ""
echo "已同步的目标："
echo "  ✓ Claude Code 项目级 (.claude/skills/) ← 主要"
echo "  ✓ Claude Code 全局 (~/.claude/skills/) ← 参考"
echo "  ✓ Codex (~/.codex/skills/)"
echo "  ✓ Gemini CLI (extension)"
