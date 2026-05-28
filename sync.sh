#!/bin/bash
# Universal Skills 同步脚本 v2
# 将 ~/universal-skills 同步 to 各 AI Coding 工具

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

# 扫描某个技能目录，把不在 categories/ 里的技能自动 import 到 categories/imported/
# 用法: import_orphans <skills_dir> <source_label>
import_orphans() {
    local skills_dir="$1"
    local source_label="$2"
    local imported=0

    [ -d "$skills_dir" ] || return 0

    # 收集 categories/ 中所有已知技能名
    local known_skills
    known_skills=$(find "$UNIVERSAL_SKILLS/categories" -type f -name "SKILL.md" -exec dirname {} \; | xargs -I{} basename {} | sort)

    # 遍历 skills_dir 中每个含 SKILL.md 的子目录
    while IFS= read -r -d '' skill_md; do
        local skill_dir skill_name
        skill_dir="$(dirname "$skill_md")"
        skill_name="$(basename "$skill_dir")"

        # 如果 categories/ 里已有同名技能，跳过
        if echo "$known_skills" | grep -qx "$skill_name"; then
            continue
        fi

        # 否则 import 到 categories/imported/
        local dest="$UNIVERSAL_SKILLS/categories/imported/$skill_name"
        if [ ! -d "$dest" ]; then
            mkdir -p "$UNIVERSAL_SKILLS/categories/imported"
            cp -r "$skill_dir" "$dest"
            warn "  ↑ 发现孤立技能 [$source_label] $skill_name → 已 import 到 categories/imported/"
            imported=$((imported + 1))
            # 更新 known_skills 避免重复 import
            known_skills=$(printf '%s\n%s' "$known_skills" "$skill_name")
        fi
    done < <(find "$skills_dir" -maxdepth 2 -type f -name "SKILL.md" -print0)

    if [ $imported -gt 0 ]; then
        warn "  已自动 import $imported 个孤立技能到 categories/imported/，请 git add & commit"
    fi
}

# 同步到全局 Claude（保留，用于某些情况）
sync_claude_global() {
    local target="$HOME/.claude/skills"

    # 先扫描孤立技能，import 到 categories/ 再继续
    import_orphans "$target" "Claude Code"

    if [ -d "$target" ] && [ ! -L "$target" ]; then
        backup "$target"
        rm -rf "$target"
    fi

    mkdir -p "$target"
    
    local skill_count=0
    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
            local skill_name="$(basename "$skill_dir")"
            cp -r "$skill_dir" "$target/$skill_name"
            skill_count=$((skill_count + 1))
        fi
    done

    success "Claude Code 全局 skills 已同步 (~/.claude/skills/)"
    warn "  注意: Claude Code 主要加载项目级 skills，全局目录仅供参考"
}

# 自动发现所有包含 .claude 目录的项目
discover_projects() {
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

    # 也搜索常见项目目录和 worktrees 目录
    for base_dir in "$HOME/code" "$HOME/projects" "$HOME/work" "$HOME/Documents" "$HOME/xiyu/worktrees"; do
        if [ -d "$base_dir" ]; then
            while IFS= read -r -d '' project_dir; do
                if [ -d "$project_dir/.claude" ]; then
                    found_projects+=("$project_dir")
                fi
            done < <(find "$base_dir" -maxdepth 1 -type d -print0 2>/dev/null)
        fi
    done

    # 去重
    unique_projects=($(printf "%s\n" "${found_projects[@]}" | sort -u))
}

# 同步到项目级 Claude（这才是真正有用的）
sync_claude_projects() {
    local synced_count=0
    local skill_count_total=0

    # 自动发现所有包含 .claude 目录的项目
    discover_projects

    log "发现 ${#unique_projects[@]} 个包含 .claude 的项目"

    for project_dir in "${unique_projects[@]}"; do
        local project_name="$(basename "$project_dir")"
        local skills_dir="$project_dir/.claude/skills"

        # 创建 skills 目录
        mkdir -p "$skills_dir"

        # 清理旧的分类目录 (若存在)
        for category_dir in "$UNIVERSAL_SKILLS/categories"/*; do
            if [ -d "$category_dir" ]; then
                local category_name="$(basename "$category_dir")"
                rm -rf "$skills_dir/$category_name"
            fi
        done

        # 同步技能 (扁平化复制，以兼容 Claude Code 技能解析)
        local skill_count=0
        for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
            if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
                local skill_name="$(basename "$skill_dir")"
                rm -rf "$skills_dir/$skill_name"
                cp -r "$skill_dir" "$skills_dir/$skill_name"
                ((skill_count++))
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

# 同步到项目级 Cursor (.cursor/rules/)
sync_cursor_projects() {
    local synced_count=0
    local skill_count_total=0

    if [ -z "${unique_projects+x}" ]; then
        discover_projects
    fi

    for project_dir in "${unique_projects[@]}"; do
        local project_name="$(basename "$project_dir")"
        local cursor_rules_dir="$project_dir/.cursor/rules"

        # 创建 .cursor/rules 目录
        mkdir -p "$cursor_rules_dir"

        # 清理旧的 .mdc 技能文件
        for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
            if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
                local skill_name="$(basename "$skill_dir")"
                rm -f "$cursor_rules_dir/$skill_name.mdc"
            fi
        done

        # 拷贝扁平化的技能并重命名为 .mdc 格式
        local skill_count=0
        for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
            if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
                local skill_name="$(basename "$skill_dir")"
                cat "$skill_dir/SKILL.md" > "$cursor_rules_dir/$skill_name.mdc"
                ((skill_count++))
            fi
        done

        if [ $skill_count -gt 0 ]; then
            log "  → $project_name (Cursor Rules): $skill_count 个技能"
            synced_count=$((synced_count + 1))
            skill_count_total=$((skill_count_total + skill_count))
        fi
    done

    if [ $synced_count -gt 0 ]; then
        success "已同步 $synced_count 个项目的 Cursor rules ($skill_count_total 个 rule 文件)"
    fi
}

# 同步到 Codex
sync_codex() {
    local target="$HOME/.codex/skills"

    if [ ! -d "$HOME/.codex" ]; then
        return
    fi

    # 先扫描孤立技能，import 到 categories/ 再继续
    import_orphans "$target" "Codex"

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

# 同步到项目级 skills（为 Gemini/Gemini in projects）
sync_projects() {
    local synced_count=0

    # 需要同步的项目列表
    local projects=(
        "$HOME/clawd"
        "$HOME/clawd-work"
        "$HOME/nexusarchive"
        "$HOME/everything-claude-code"
        "$HOME/JLAF"
        "$HOME/PLM"
        "$HOME/zhitoujianli"
        "$HOME/liujie"
        "$HOME/xiyu/xiyu-bid-poc"
    )

    # 动态添加 xiyu 的 worktrees
    if [ -d "$HOME/xiyu/worktrees" ]; then
        while IFS= read -r -d '' wt; do
            projects+=("$wt")
        done < <(find "$HOME/xiyu/worktrees" -maxdepth 1 -mindepth 1 -type d -print0 2>/dev/null)
    fi

    for project_dir in "${projects[@]}"; do
        if [ ! -d "$project_dir" ]; then
            continue
        fi

        local project_name="$(basename "$project_dir")"
        local skills_dir="$project_dir/skills"

        # 检查项目是否有 skills 目录
        if [ ! -d "$skills_dir" ]; then
            continue
        fi

        # 创建 universal-skills symlink
        local symlink="$skills_dir/universal-skills"

        # 删除旧的 symlink 或文件
        if [ -L "$symlink" ]; then
            rm -f "$symlink"
        elif [ -e "$symlink" ]; then
            warn "$project_name: universal-skills 是目录，跳过"
            continue
        fi

        # 创建 symlink
        ln -sf "$UNIVERSAL_SKILLS/categories" "$symlink"
        log "✓ $project_name: universal-skills symlink 已创建"
        synced_count=$((synced_count + 1))
    done

    if [ $synced_count -gt 0 ]; then
        success "已同步 $synced_count 个项目的 universal-skills symlink"
    else
        log "未找到需要同步的项目"
    fi
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

# 同步到 Antigravity (通过 Gemini Extension GEMINI.md)
sync_antigravity() {
    local extension_src="$UNIVERSAL_SKILLS/gemini-extension/universal-skills"
    local extension_install="$HOME/.gemini/extensions/universal-skills"
    local enablement_file="$HOME/.gemini/extensions/extension-enablement.json"

    # 1. 检查 GEMINI.md 是否存在于 extension 源目录
    if [ ! -f "$extension_src/GEMINI.md" ]; then
        warn "Antigravity: GEMINI.md 缺失于 $extension_src"
        return 1
    fi

    # 2. 检查 extension 是否已安装（symlink 到源目录）
    if [ ! -d "$extension_install" ]; then
        warn "Antigravity: universal-skills extension 未安装"
        warn "  请运行: gemini extensions link \"$extension_src\""
        return 1
    fi

    # 3. 检查 extension 是否为 symlink（链接式安装）
    local install_json="$extension_install/.gemini-extension-install.json"
    if [ -f "$install_json" ]; then
        local install_type
        install_type=$(python3 -c "import json,sys; d=json.load(open('$install_json')); print(d.get('type',''))" 2>/dev/null)
        if [ "$install_type" = "link" ]; then
            log "  Antigravity extension 为 link 模式，GEMINI.md 实时生效"
        fi
    fi

    # 4. 确保 extension-enablement.json 包含 universal-skills
    if [ -f "$enablement_file" ]; then
        if ! python3 -c "import json,sys; d=json.load(open('$enablement_file')); sys.exit(0 if 'universal-skills' in d else 1)" 2>/dev/null; then
            warn "Antigravity: universal-skills 未在 extension-enablement.json 中启用"
            warn "  请在 Antigravity 中手动启用该 extension"
        fi
    fi

    # 5. 统计技能数量
    local skill_count
    skill_count=$(find "$UNIVERSAL_SKILLS/categories" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')

    success "Antigravity extension 已就绪 ($skill_count 个技能，通过 GEMINI.md 注入)"
    log "  GEMINI.md: $extension_src/GEMINI.md"
}

# 同步到 Claude Code 插件 (Skill tool 需要)
sync_plugin() {
    local plugin_dir="$HOME/.claude/plugins/cache/local/universal-skills"
    local version="1.0.0"

    # 创建插件目录结构
    mkdir -p "$plugin_dir/$version"

    # 创建 .claude-plugin/plugin.json (如果不存在)
    if [ ! -f "$UNIVERSAL_SKILLS/.claude-plugin/plugin.json" ]; then
        mkdir -p "$UNIVERSAL_SKILLS/.claude-plugin"
        cat > "$UNIVERSAL_SKILLS/.claude-plugin/plugin.json" << 'EOF'
{
  "name": "universal-skills",
  "description": "Universal AI Coding Skills - synchronizes across Claude Code, Codex, and Gemini CLI. Covers languages (Python, Go, Swift, Java, C++), frameworks (Django, Spring Boot), patterns (TDD, E2E, API design), security, and deployment.",
  "version": "1.0.0",
  "author": {
    "name": "universal-skills"
  },
  "keywords": ["skills", "tdd", "python", "golang", "swift", "django", "spring-boot", "security", "testing", "architecture"]
}
EOF
    fi

    # 创建 symlinks (扁平化以兼容 Claude Code 技能解析)
    rm -f "$plugin_dir/$version/.claude-plugin"
    rm -rf "$plugin_dir/$version/skills"

    ln -sf "$UNIVERSAL_SKILLS/.claude-plugin" "$plugin_dir/$version/.claude-plugin"
    mkdir -p "$plugin_dir/$version/skills"

    # 为每个技能创建单独的 symlink
    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
            local skill_name="$(basename "$skill_dir")"
            ln -sf "$skill_dir" "$plugin_dir/$version/skills/$skill_name"
        fi
    done

    # 统计技能数量
    local skill_count=$(find -L "$plugin_dir/$version/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')

    success "Claude Code 插件已同步 ($skill_count 个技能)"
    log "  技能路径: $plugin_dir/$version/skills/"
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
    sync_plugin
    echo ""
fi

if [ "$SKIP_PROJECTS" = false ]; then
    sync_claude_projects
    sync_cursor_projects
    sync_projects
    echo ""
fi

if [ "$SKIP_CODEX" = false ]; then
    sync_codex
    echo ""
fi

if [ "$SKIP_GEMINI" = false ]; then
    sync_gemini
    sync_antigravity
    echo ""
fi

success "同步完成！"
echo ""
echo "提示："
echo "  - 本地自定义技能: $UNIVERSAL_SKILLS/local/"
echo "  - 备份位置: $BACKUP_DIR"
[ "$SKIP_GLOBAL" = false ] && echo "  - ⚠️  重启 Claude Code 以加载新 skills / 插件"
echo ""
echo "已同步的目标："
[ "$SKIP_GLOBAL" = false ] && echo "  ✓ Claude Code 插件 (~/.claude/plugins/cache/local/universal-skills/)"
[ "$SKIP_GLOBAL" = false ] && echo "  ✓ Claude Code 全局 (~/.claude/skills/) ← 参考"
[ "$SKIP_PROJECTS" = false ] && echo "  ✓ Claude Code 项目级 (.claude/skills/) ← 主要"
[ "$SKIP_PROJECTS" = false ] && echo "  ✓ Cursor 项目级 (.cursor/rules/) ← Cursor Rules"
[ "$SKIP_CODEX" = false ] && echo "  ✓ Codex (~/.codex/skills/)"
[ "$SKIP_GEMINI" = false ] && echo "  ✓ Gemini CLI (extension)"
[ "$SKIP_GEMINI" = false ] && echo "  ✓ Antigravity (GEMINI.md 注入到 ~/.gemini/extensions/universal-skills/)"
[ "$SKIP_PROJECTS" = false ] && echo "  ✓ 项目级 symlinks (clawd, xiyu, etc.)"
echo ""
