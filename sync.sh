#!/bin/bash
# Universal Skills 同步脚本
# 用于将 ~/universal-skills 同步到各 AI Coding 工具

set -e

UNIVERSAL_SKILLS="$HOME/universal-skills"
BACKUP_DIR="$UNIVERSAL_SKILLS/.backup"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

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

# 同步到 Claude Code
sync_claude() {
    local target="$HOME/.claude/skills"

    # 先扫描孤立技能，import 到 categories/ 再继续
    import_orphans "$target" "Claude Code"

    if [ -d "$target" ] && [ ! -L "$target" ]; then
        backup "$target"
        rm -rf "$target"
    fi

    # 重新创建目标目录
    mkdir -p "$target"

    # 复制整个 categories 内容到 target（包含隐藏目录，如 .system）
    cp -a "$UNIVERSAL_SKILLS/categories"/. "$target"/

    success "Claude Code skills 已同步"
}

# 同步到 Codex
sync_codex() {
    local target="$HOME/.codex/skills"

    # 先扫描孤立技能，import 到 categories/ 再继续
    import_orphans "$target" "Codex"

    if [ -d "$target" ] && [ ! -L "$target" ]; then
        backup "$target"
    fi

    # 清空并重新创建目标目录
    rm -rf "$target"
    mkdir -p "$target"

    # 复制所有 universal-skills 到 Codex
    local skill_count=0

    # 遍历 categories 下所有包含 SKILL.md 的目录（包含隐藏目录，如 .system）
    while IFS= read -r -d '' skill_md; do
        local skill_dir
        local skill_name
        skill_dir="$(dirname "$skill_md")"
        skill_name="$(basename "$skill_dir")"

        # 避免重名技能重复复制
        if [ -d "$target/$skill_name" ]; then
            continue
        fi

        cp -r "$skill_dir" "$target/$skill_name"
        skill_count=$((skill_count + 1))
    done < <(find "$UNIVERSAL_SKILLS/categories" -type f -name "SKILL.md" -print0)

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
        "$HOME/xiyu"
    )

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
        warn "Gemini CLI 未安装，跳过"
        return
    fi

    local extension_dir="$UNIVERSAL_SKILLS/gemini-extension/universal-skills"

    # 确保 gemini-extension.json 存在
    if [ ! -f "$extension_dir/gemini-extension.json" ]; then
        warn "Gemini extension 配置缺失，跳过"
        return
    fi

    # 检查是否已安装
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

    # 创建 symlinks
    rm -f "$plugin_dir/$version/.claude-plugin"
    rm -f "$plugin_dir/$version/skills"

    ln -sf "$UNIVERSAL_SKILLS/.claude-plugin" "$plugin_dir/$version/.claude-plugin"
    ln -sf "$UNIVERSAL_SKILLS/categories" "$plugin_dir/$version/skills"

    # 统计技能数量
    local skill_count=$(find -L "$plugin_dir/$version/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')

    success "Claude Code 插件已同步 ($skill_count 个技能)"
    log "  技能路径: $plugin_dir/$version/skills/"
}

# 创建本地覆盖目录
mkdir -p "$UNIVERSAL_SKILLS/local"

log "开始同步 Universal Skills..."
echo ""

sync_claude
sync_codex
sync_plugin
sync_gemini
sync_antigravity
sync_projects

echo ""
success "同步完成！"
echo ""
echo "提示："
echo "  - 本地自定义技能放在: $UNIVERSAL_SKILLS/local/"
echo "  - 备份位置: $BACKUP_DIR"
echo "  - 重启 Claude Code 以加载新插件"
echo ""
echo "已同步的工具："
echo "  ✓ Claude Code 插件 (~/.claude/plugins/cache/local/universal-skills/)"
echo "  ✓ Claude Code skills (~/.claude/skills/) - 兼容模式"
echo "  ✓ Codex (~/.codex/skills/)"
echo "  ✓ Gemini CLI (extension + project symlinks)"
echo "  ✓ Antigravity (GEMINI.md 注入到 ~/.gemini/extensions/universal-skills/)"
echo "  ✓ 项目级 (clawd, xiyu, etc.)"
