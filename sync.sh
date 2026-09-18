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

# 已合并/别名技能：保留源码目录，但不同步为独立入口，避免工具侧重复触发。
DUPLICATE_SKILL_NAMES=(
    "google-style-code-review"
)

# 已删除的过期技能：即使项目/工具副本里还有残留，也绝不重新 import。
# （2026-09-10：gstack-codex 等是 imported/ 里的旧副本，与 gstack/ 下正版重名，
# 删仓库后若不拉黑，import_orphans 会把 21 个项目的实体残留又捡回来。）
STALE_ORPHAN_DENYLIST=(
    "gstack"
    "gstack-codex"
    "gstack-connect-chrome"
    "gstack-gstack-upgrade"
    "connect-chrome"
    "using-superpowers"
)

is_stale_orphan() {
    local skill_name="$1"
    local stale

    for stale in "${STALE_ORPHAN_DENYLIST[@]}"; do
        if [ "$skill_name" = "$stale" ]; then
            return 0
        fi
    done

    return 1
}

# 项目专用技能：格式为 "技能名:项目名匹配模式"，匹配模式支持 bash 通配符
# 这些技能不会同步到全局目录，只会同步到项目名匹配的项目级 skills 目录
PROJECT_ONLY_SKILLS=()

is_duplicate_skill_name() {
    local skill_name="$1"
    local duplicate

    for duplicate in "${DUPLICATE_SKILL_NAMES[@]}"; do
        if [ "$skill_name" = "$duplicate" ]; then
            return 0
        fi
    done

    return 1
}

# 判断技能是否为项目专用技能，若是则输出匹配模式，否则返回非0
get_project_only_pattern() {
    local skill_name="$1"
    local entry s_name pattern

    for entry in "${PROJECT_ONLY_SKILLS[@]}"; do
        s_name="${entry%%:*}"
        pattern="${entry#*:}"
        if [ "$skill_name" = "$s_name" ]; then
            echo "$pattern"
            return 0
        fi
    done

    return 1
}

# 判断技能是否为项目专用（全局同步时需跳过）
is_project_only_skill() {
    local skill_name="$1"
    get_project_only_pattern "$skill_name" > /dev/null
}

# 判断项目专用技能是否允许在指定项目中同步
# is_skill_allowed_for_project <skill_name> <project_name_or_path>
#
# 支持两种匹配模式：
#   A. pattern 是通配符（如 "xiyu*"）→ 只匹配 project 的 basename
#   B. 但更严格：如果 pattern 是通配符形如 "xiyu*"，还额外允许项目目录的真实路径
#      中包含 /xiyu/ 或 /xiyu-bid-，这是为了识别 git worktrees 下的 xiyu 项目
#      （worktree 目录名常被人命名为 trae/cursor/grok 而不是 xiyu*，但真实父目录
#       仍在 ~/xiyu/ 下）
is_skill_allowed_for_project() {
    local skill_name="$1"
    local project_input="$2"
    local pattern
    local project_name
    local project_real=""

    pattern=$(get_project_only_pattern "$skill_name") || return 0  # 非 project-only 技能，允许

    # project_input 可能只是项目名，也可能是完整路径
    if [[ "$project_input" == /* ]]; then
        # 完整路径：realpath
        project_real=$(cd "$project_input" 2>/dev/null && pwd -P || echo "$project_input")
        project_name=$(basename "$project_real")
    else
        project_name="$project_input"
    fi

    # 匹配 1：project_name 本身匹配 pattern（原逻辑）
    # shellcheck disable=SC2053
    if [[ "$project_name" == $pattern ]]; then
        return 0
    fi

    # 匹配 2（增强）：如果 pattern 形如 "xiyu*"（西域项目族），则只要项目真实路径
    # 包含 /xiyu/ 也判定为匹配（覆盖 xiyu worktrees 目录被命名为 trae / cursor / zcode 等情况）
    if [[ "$pattern" == xiyu\* ]]; then
        if [ -n "$project_real" ] && [[ "$project_real" == */xiyu/* ]]; then
            return 0
        fi
    fi

    return 1
}

is_syncable_skill_dir() {
    local skill_dir="$1"
    local skill_name

    [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ] || return 1

    skill_name="$(basename "$skill_dir")"
    ! is_duplicate_skill_name "$skill_name"
}

# Codex desktop/Copilot 与 ZCode 共用 ~/.agents/skills/ 作为跨运行时技能入口。
# 当共享入口已经提供同名技能时，~/.codex/skills/ 不应再注册一份，
# 否则宿主会把同一套 SKILL.md 描述计算两次并触发 context budget fallback。
is_shared_agent_skill() {
    local skill_name="$1"
    [ -f "$HOME/.agents/skills/$skill_name/SKILL.md" ]
}

# 项目级 .agents/skills 去重：Codex 会同时加载 USER(~/.agents/skills) 与
# REPO($CWD/.agents/skills) 两个 scope，且同名不合并、选择器里并列展示
# （"个人 + 项目名"双条目）。用户级已有的技能不再往项目级拷。
is_user_level_agent_skill() {
    local skill_name="$1"
    [ -f "$HOME/.agents/skills/$skill_name/SKILL.md" ]
}

# 清理工具入口（Codex/Qoder 等）中由 universal-skills 管理、且已被 ~/.agents/skills/ 覆盖的重复项。
# Codex 与 qoder-cn 都会同时加载自己的 skills 目录和 ~/.agents/skills/，
# 同名技能会在宿主侧产生 "overrides same-source skill" 告警噪声。
# - universal symlink：直接删除链接（可由下一次切换配置恢复）
# - 完全相同的实体副本：移动到 .backup，而不是不可恢复删除
# - 内容不同的实体副本：保留并报警，避免覆盖工具管理的技能
prune_shared_duplicates() {
    local target="$1"
    local label="${2:-Shared}"
    local shared_root="$HOME/.agents/skills"
    local entry skill_name shared_skill dest backup_root removed moved
    removed=0
    moved=0

    [ -d "$shared_root" ] || return 0

    for entry in "$target"/*; do
        [ -e "$entry" ] || [ -L "$entry" ] || continue
        skill_name="$(basename "$entry")"
        [ "$skill_name" = ".system" ] && continue
        shared_skill="$shared_root/$skill_name"
        [ -f "$shared_skill/SKILL.md" ] || continue

        if [ -L "$entry" ]; then
            dest="$(readlink "$entry" 2>/dev/null || true)"
            if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                rm -f "$entry"
                removed=$((removed + 1))
            fi
        elif [ -d "$entry" ] && [ -f "$entry/SKILL.md" ]; then
            if diff -rq "$entry" "$shared_skill" >/dev/null 2>&1; then
                if [ -z "${backup_root:-}" ]; then
                    backup_root="$BACKUP_DIR/$(printf '%s' "$label" | tr '[:upper:]' '[:lower:]')-shared-$(date +%Y%m%d-%H%M%S)"
                    mkdir -p "$backup_root"
                fi
                mv "$entry" "$backup_root/$skill_name"
                moved=$((moved + 1))
            else
                warn "$label 重复技能 [$skill_name] 与 ~/.agents/skills/ 内容不同，保留 $label 实体副本"
            fi
        fi
    done

    [ "$removed" -gt 0 ] && log "$label 共享入口重复 symlink 已清理 ($removed 个)"
    [ "$moved" -gt 0 ] && log "$label 共享入口重复实体副本已移入备份 ($moved 个): ${backup_root}"
    return 0
}

# 增量复制单个技能（增量校验重试核心）
# 幂等：目标已是最新（diff 一致）或 symlink 直指源 → 跳过；漂移/缺失 → 重拷
# 返回值：0=已复制  1=无需变动（已一致）
# sync_skill_copy <src_skill_dir> <dst_skill_dir>
sync_skill_copy() {
    local src="$1"
    local dst="$2"

    if [ -L "$dst" ]; then
        local dest
        dest="$(readlink "$dst" 2>/dev/null || true)"
        if [ "$dest" = "$src" ]; then
            return 1
        fi
        rm -f "$dst"
    elif [ -e "$dst" ]; then
        if diff -rq "$src" "$dst" >/dev/null 2>&1; then
            return 1
        fi
        rm -rf "$dst"
    fi

    cp -R "$src" "$dst"
    return 0
}

cleanup_duplicate_skill_links() {
    local target="$1"
    local removed=0
    local skill_name link dest

    [ -d "$target" ] || {
        echo 0
        return 0
    }

    for skill_name in "${DUPLICATE_SKILL_NAMES[@]}"; do
        link="$target/$skill_name"
        if [ -L "$link" ]; then
            dest="$(readlink "$link")"
            if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                rm -f "$link"
                removed=$((removed + 1))
            fi
        fi
    done

    echo "$removed"
}

cleanup_dead_universal_links() {
    local target="$1"
    [ -d "$target" ] || return 0

    for entry in "$target"/*; do
        [ -e "$entry" ] || [ -L "$entry" ] || continue
        if [ -L "$entry" ]; then
            local dest
            dest="$(readlink "$entry" 2>/dev/null || true)"
            if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                if [ ! -e "$entry" ] || [ ! -e "$dest" ]; then
                    rm -f "$entry"
                fi
            fi
        fi
    done
    return 0
}

# 创建备份（自动清理旧备份，保留最新 2 份）
backup() {
    local dir="$1"
    if [ -d "$dir" ] && [ ! -L "$dir" ]; then
        mkdir -p "$BACKUP_DIR"
        local backup_name="$(basename "$dir")-$(date +%Y%m%d-%H%M%S)"
        log "备份 $dir 到 $BACKUP_DIR/$backup_name"
        cp -R "$dir" "$BACKUP_DIR/$backup_name"

        # 自动清理：保留最新 2 份备份
        local keep=2
        local count=0
        while IFS= read -r -d '' bak; do
            count=$((count + 1))
            if [ $count -gt $keep ]; then
                rm -rf "$bak"
                log "清理旧备份: $(basename "$bak")"
            fi
        done < <(find "$BACKUP_DIR" -maxdepth 1 -type d -name "skills-*" -print0 2>/dev/null | sort -zr)
    fi
}

# 扫描某个技能目录，把不在 categories/ 里的技能自动 import 到 categories/imported/
# 用法: import_orphans <skills_dir> <source_label> [--scan-subdirs]
import_orphans() {
    local skills_dir="$1"
    local source_label="$2"
    local scan_subdirs="${3:-}"
    local imported=0

    [ -d "$skills_dir" ] || return 0

    # 收集 categories/ 中所有已知技能名
    local known_skills
    known_skills=$(find "$UNIVERSAL_SKILLS/categories" -type f -name "SKILL.md" -exec dirname {} \; | xargs -I{} basename {} | sort)

    # 选择查找深度：单个目录或递归子目录
    local find_cmd
    if [ "$scan_subdirs" = "--scan-subdirs" ]; then
        find_cmd="find \"$skills_dir\" -maxdepth 3 -type f -name \"SKILL.md\" -print0"
    else
        find_cmd="find \"$skills_dir\" -maxdepth 2 -type f -name \"SKILL.md\" -print0"
    fi

    # 遍历 skills_dir 中每个含 SKILL.md 的子目录
    while IFS= read -r -d '' skill_md; do
        local skill_dir skill_name
        skill_dir="$(dirname "$skill_md")"
        skill_name="$(basename "$skill_dir")"

        # 跳过自身和 system 内部技能
        if [ "$skill_name" = "imported" ] || [ "$skill_name" = ".system" ]; then
            continue
        fi

        # 拉黑已删除的过期技能：项目残留副本不得复活
        if is_stale_orphan "$skill_name"; then
            continue
        fi

        # 容器目录不是技能：内部还嵌套着别的 SKILL.md（如整个 gstack 仓库被拷进来），
        # 当单技能 import 会污染命名空间并造成大面积重名，跳过
        if find "$skill_dir" -mindepth 2 -name "SKILL.md" -print -quit 2>/dev/null | grep -q .; then
            warn "  跳过容器目录 [$source_label] $skill_name（内部嵌套多技能，非单一技能）"
            continue
        fi

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
    done < <(eval "$find_cmd")

    if [ $imported -gt 0 ]; then
        warn "  已自动 import $imported 个孤立技能到 categories/imported/，请 git add & commit"
    fi
}

# 反向回流：扫描各项目 skills 目录，找出与 categories/ 同名但有差异的技能
# 用法: pull_from_projects [--dry-run]
# --dry-run: 只展示差异，不回流

# 查找 categories/ 中的同名技能目录（兼容 bash 3.x）
# 如果有多个同名技能，选 diff 行数最少（内容最接近）的那个
find_repo_skill_dir() {
    local skill_name="$1"
    local best_dir=""
    local best_diff_lines=999999
    local project_md="$2"  # 可选：项目版路径，用于选最接近的

    for cat_dir in "$UNIVERSAL_SKILLS/categories"/*/; do
        local candidate="${cat_dir}${skill_name}"
        [ -f "$candidate/SKILL.md" ] || continue

        if [ -z "$project_md" ]; then
            # 没提供项目版，返回第一个匹配
            echo "$candidate"
            return 0
        fi

        # 有项目版，选 diff 行数最少的
        local lines
        lines=$(diff "$candidate/SKILL.md" "$project_md" 2>/dev/null | grep -c '^[<>]')
        if [ "$lines" -lt "$best_diff_lines" ]; then
            best_diff_lines=$lines
            best_dir="$candidate"
        fi
    done

    if [ -n "$best_dir" ]; then
        echo "$best_dir"
        return 0
    fi
    return 1
}

pull_from_projects() {
    local dry_run="${1:-}"
    local local_dir_names=(".claude" ".trae" ".trae-cn" ".agents")

    # 收集项目列表（复用 discover_projects + sync_projects 的项目列表）
    local projects=()
    discover_projects
    for project_dir in "${unique_projects[@]}"; do
        projects+=("$project_dir")
    done
    for base in "$HOME/clawd" "$HOME/clawd-work" "$HOME/nexusarchive" \
                "$HOME/everything-claude-code" "$HOME/JLAF" "$HOME/PLM" \
                "$HOME/zhitoujianli" "$HOME/liujie" "$HOME/mimo" \
                "$HOME/xiyu/xiyu-bid-poc"; do
        [ -d "$base" ] && projects+=("$base")
    done
    if [ -d "$HOME/xiyu/worktrees" ]; then
        while IFS= read -r -d '' wt; do
            projects+=("$wt")
        done < <(find "$HOME/xiyu/worktrees" -maxdepth 1 -mindepth 1 -type d -print0 2>/dev/null)
    fi

    # 去重
    local unique_pjs=($(printf '%s\n' "${projects[@]}" | sort -u))

    # 扫描
    local diffs=0
    local diff_list=""  # 换行分隔的记录

    for project_dir in "${unique_pjs[@]}"; do
        local project_name="$(basename "$project_dir")"
        for dir_name in "${local_dir_names[@]}"; do
            local skills_dir="$project_dir/$dir_name/skills"
            [ -d "$skills_dir" ] || continue

            for skill_md in "$skills_dir"/*/SKILL.md; do
                [ -f "$skill_md" ] || continue
                local skill_name="$(basename "$(dirname "$skill_md")")"

                # 查找 categories/ 中的同名技能（选内容最接近的）
                local repo_dir
                repo_dir=$(find_repo_skill_dir "$skill_name" "$skill_md") || continue

                local repo_md="$repo_dir/SKILL.md"

                # 比较
                if ! diff -q "$repo_md" "$skill_md" > /dev/null 2>&1; then
                    diffs=$((diffs + 1))
                    local project_skill_dir="$(dirname "$skill_md")"
                    diff_list="${diff_list}${skill_name}|${project_name}|${dir_name}|${project_skill_dir}|${repo_dir}
"
                    warn "[$project_name/$dir_name] $skill_name"
                    local dlines
                    dlines=$(diff "$repo_md" "$skill_md" 2>/dev/null | grep -c '^[<>]')
                    echo "  差异行数: ${dlines:-0} (完整 diff 见确认时展示)"
                    echo "  ---"
                fi
            done
        done
    done

    if [ $diffs -eq 0 ]; then
        success "没有发现同名技能差异，所有项目副本与仓库一致"
        return 0
    fi

    warn "共发现 $diffs 个同名技能有差异"
    echo ""

    if [ "$dry_run" = "--dry-run" ]; then
        log "（--dry-run 模式，不回流）"
        return 0
    fi

    # 逐个确认回流；每个技能先展示完整 diff，明示覆盖语义
    local pulled=0
    local skipped=0
    while IFS='|' read -r skill_name project_name dir_name project_skill_dir repo_dir; do
        [ -z "$skill_name" ] && continue

        echo ""
        echo -e "${CYAN}==> $skill_name${NC} (来自 $project_name/$dir_name)"

        # 判断差异方向：仓库是否已有项目版没有的内容
        local repo_only anchor
        repo_only=$(diff --old-line-format='%<' --new-line-format='' --unchanged-line-format='' \
                    "$repo_dir/SKILL.md" "$project_skill_dir/SKILL.md" 2>/dev/null)
        if [ -n "$repo_only" ]; then
            warn "  注意: 仓库版包含项目版没有的内容，整份覆盖将丢弃这些行！"
            anchor="双向差异(部分覆盖有风险)"
        else
            anchor="仅项目版新增(可安全合并)"
        fi

        echo "  [$anchor] 以下为 仓库版< 项目版> 差异:"
        diff "$repo_dir/SKILL.md" "$project_skill_dir/SKILL.md" 2>/dev/null | while IFS= read -r l; do
            echo "    $l"
        done
        echo ""

        local answer=""
        read -p "  回流此技能到仓库？[y/N/a(全部采用项目版)/m(行级合并)/q(退出)] " -r answer
        case "$answer" in
            [Qq]) break ;;
            [Aa])
                while IFS='|' read -r sn pn dn psd rd; do
                    [ -z "$sn" ] && continue
                    cp "$psd/SKILL.md" "$rd/SKILL.md"
                    for f in "$psd"/*; do
                        [ "$(basename "$f")" = "SKILL.md" ] && continue
                        cp -R "$f" "$rd/"
                    done
                    success "  已回流(整份覆盖) $sn"
                    pulled=$((pulled + 1))
                done <<< "$diff_list"
                break
                ;;
            [Mm])
                if merge_skill_file "$repo_dir/SKILL.md" "$project_skill_dir/SKILL.md"; then
                    for f in "$project_skill_dir"/*; do
                        [ "$(basename "$f")" = "SKILL.md" ] && continue
                        cp -R "$f" "$repo_dir/" 2>/dev/null
                    done
                    success "  已行级合并 $skill_name"
                    pulled=$((pulled + 1))
                else
                    skipped=$((skipped + 1))
                fi
                ;;
            [Yy])
                cp "$project_skill_dir/SKILL.md" "$repo_dir/SKILL.md"
                for f in "$project_skill_dir"/*; do
                    [ "$(basename "$f")" = "SKILL.md" ] && continue
                    cp -R "$f" "$repo_dir/"
                done
                success "  已回流(整份覆盖) $skill_name"
                pulled=$((pulled + 1))
                ;;
        esac
    done <<< "$diff_list"

    if [ $pulled -gt 0 ]; then
        success "已回流 $pulled 个技能到仓库"
        warn "请运行: git diff 检查变更，然后 git add & commit"
    else
        log "未回流任何技能"
    fi
    [ $skipped -gt 0 ] && warn "$skipped 个技能因合并冲突被跳过，请手动处理"
}

# 行级合并：以仓库 git 历史为 base 做三向合并
# 返回 0 = 合并成功写入 repo_md；1 = 冲突需人工（已保留仓库版不动）
# 用法: merge_skill_file <repo_sk.md> <project_sk.md>
merge_skill_file() {
    local repo_md="$1"
    local project_md="$2"

    # 三向合并需要 diff3
    if ! command -v diff3 > /dev/null 2>&1; then
        warn "  diff3 不可用，无法行级合并；请改用整份覆盖或手动处理"
        return 1
    fi

    # base: 仓库版在 git 中的版本。若文件未跟踪，用仓库版本地内容作为 base
    local base_md=""
    if [ -n "$UNIVERSAL_SKILLS" ] && git -C "$UNIVERSAL_SKILLS" rev-parse -q --verify HEAD > /dev/null 2>&1; then
        local rel
        rel=$(git -C "$UNIVERSAL_SKILLS" ls-files "$repo_md")
        if [ -n "$rel" ]; then
            base_md=$(git -C "$UNIVERSAL_SKILLS" show "HEAD:$rel" 2>/dev/null)
        fi
    fi
    [ -z "$base_md" ] && base_md=$(cat "$repo_md")

    # 三向合并。合并源文本需要文件路径，用临时目录
    local tmpdir
    tmpdir=$(mktemp -d)
    printf '%s\n' "$base_md" > "$tmpdir/base"
    cat "$repo_md" > "$tmpdir/ours"
    cat "$project_md" > "$tmpdir/theirs"

    # 三向合并前，先记录两边「独有行」集合，供合并后校验（diff3 对相邻改动会静默丢行）
    # 兼容 BSD/macOS diff: diff base ours 中 "> " 开头是 ours 独有（相对 base 新增）
    local ours_only theirs_only
    ours_only=$(diff "$tmpdir/base" "$tmpdir/ours" 2>/dev/null | sed -n 's/^> //p')
    theirs_only=$(diff "$tmpdir/base" "$tmpdir/theirs" 2>/dev/null | sed -n 's/^> //p')

    # 生成带冲突标记的合并结果
    local merged
    merged=$(diff3 -m -L "仓库版(HEAD)" -L "仓库版(当前)" -L "项目版" "$tmpdir/ours" "$tmpdir/base" "$tmpdir/theirs" 2>/dev/null)
    rm -rf "$tmpdir"

    # diff3 -m 退出码: 0=无冲突, 1=有冲突仍输出
    if grep -q '^<<<<<<<\|^=======\|^>>>>>>>' <<< "$merged" 2>/dev/null; then
        warn "  检测到合并冲突，不会覆盖；请手动处理 $repo_md"
        echo "  冲突区段预览（前20行）:"
        echo "$merged" | grep -n '^<<<<<<<\|^>>>>>>>' | head -5 -A0
        return 1
    fi

    # 校验：our 独有行与项目独有行在结果中都必须保留，否则拒绝写入
    if [ -n "$ours_only" ]; then
        while IFS= read -r line; do
            [ -z "$line" ] && continue
            grep -Fqx -- "$line" <<< "$merged" || {
                warn "  合并丢掉了仓库独有行: \"$line\"，已拒绝写入（建议改用整份覆盖或手动处理）"
                return 1
            }
        done <<< "$ours_only"
    fi
    if [ -n "$theirs_only" ]; then
        while IFS= read -r line; do
            [ -z "$line" ] && continue
            grep -Fqx -- "$line" <<< "$merged" || {
                warn "  合并丢掉了项目独有行: \"$line\"，已拒绝写入（建议改用整份覆盖或手动处理）"
                return 1
            }
        done <<< "$theirs_only"
    fi

    if [ -z "$merged" ]; then
        warn "  合并结果为空，跳过 $repo_md"
        return 1
    fi

    printf '%s\n' "$merged" > "$repo_md"
    return 0
}

# 幂等地把一个目录注册到 TOML 配置文件的 extra_skill_dirs 数组中
# 用法: register_extra_skill_dir <config_file> <dir>
register_extra_skill_dir() {
    local config_file="$1"
    local dir="$2"

    [ -f "$config_file" ] || return 0

    # 已存在则跳过（精确匹配路径）
    if grep -qE "extra_skill_dirs.*\"$dir\"" "$config_file"; then
        return 0
    fi

    if grep -qE '^extra_skill_dirs\s*=\s*\[\s*\]' "$config_file"; then
        # 空数组 → 替换为含目标路径
        python3 - "$config_file" "$dir" << 'PYEOF'
import io, re, sys
path, new_dir = sys.argv[1], sys.argv[2]
with open(path, 'r') as f:
    content = f.read()
content = re.sub(
    r'^extra_skill_dirs\s*=\s*\[\s*\]',
    f'extra_skill_dirs = ["{new_dir}"]',
    content,
    count=1,
    flags=re.MULTILINE,
)
with open(path, 'w') as f:
    f.write(content)
PYEOF
    else
        # 非空数组 → 在 ] 前插入
        python3 - "$config_file" "$dir" << 'PYEOF'
import re, sys
path, new_dir = sys.argv[1], sys.argv[2]
with open(path, 'r') as f:
    lines = f.readlines()
out = []
inserted = False
for line in lines:
    if not inserted and re.match(r'^extra_skill_dirs\s*=\s*\[', line):
        out.append(line)
        if ']' not in line:
            # 多行数组：在闭合 ] 前插入
            buf = [line]
            for nxt in lines[len(out):]:
                if ']' in nxt:
                    out.append(f'    "{new_dir}",\n')
                    out.append(nxt)
                    inserted = True
                    break
                else:
                    out.append(nxt)
            # 跳过已消费的行
            break
        else:
            # 单行数组：在 ] 前插入
            out.append(re.sub(r'\]', f'    "{new_dir}",\n]', line, count=1))
            inserted = True
            break
    else:
        out.append(line)
with open(path, 'w') as f:
    f.writelines(out)
PYEOF
    fi
}

# 同步到全局 Claude（保留，用于某些情况）
sync_claude_global() {
    local target="$HOME/.claude/skills"

    # 仅在 --discover 时扫描孤立技能
    if [ "$DO_DISCOVER" = true ]; then
        import_orphans "$target" "Claude Code"
    fi

    if [ -d "$target" ] && [ ! -L "$target" ]; then
        backup "$target"
        rm -rf "$target"
    fi

    mkdir -p "$target"
    local duplicate_removed
    duplicate_removed=$(cleanup_duplicate_skill_links "$target")
    [ "$duplicate_removed" -gt 0 ] && log "  清理 Claude 全局重复技能 symlink: $duplicate_removed 个"

    local skill_count=0
    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            # 全局同步：跳过项目专用技能
            if is_project_only_skill "$skill_name"; then
                continue
            fi
            ln -sfh "$skill_dir" "$target/$skill_name"
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

    # 需要同步的「项目级技能目录类型」:
    #   dir_name, description
    # - .claude    : Claude Code 项目级技能（发现/孤儿扫描在此）
    # - .trae      : Trae Work 项目级技能
    # - .trae-cn   : Trae CN Agent 项目级技能
    # - .agents    : ZCode / Agent 项目级技能（用户级已有同名则跳过，防 Codex 双 scope 重复展示）
    local local_dir_names=(".claude" ".trae" ".trae-cn" ".agents")

    for project_dir in "${unique_projects[@]}"; do
        local project_name="$(basename "$project_dir")"
        local any_done=false
        local project_real=""
        project_real=$(cd "$project_dir" 2>/dev/null && pwd -P || echo "$project_dir")
        # 判断项目是否属于 xiyu 族（兼容 worktree 命名为 trae/zcode 等情况）
        local project_is_xiyu=false
        [[ "$project_name" == xiyu* ]] && project_is_xiyu=true
        [[ "$project_real" == *"/xiyu/"* ]] && project_is_xiyu=true

        for dir_name in "${local_dir_names[@]}"; do
            local skills_dir="$project_dir/$dir_name/skills"

            # .claude 必创建（也是项目发现条件）；其它目录：只要是 xiyu 族项目，就主动创建；
            #                    如果项目本身已有 .trae/.trae-cn/.agents 目录（哪怕不是 xiyu*），也创建 skills
            if [ "$dir_name" = ".claude" ]; then
                mkdir -p "$skills_dir"
            elif $project_is_xiyu; then
                mkdir -p "$skills_dir"
            elif [ ! -d "$project_dir/$dir_name" ]; then
                continue
            else
                mkdir -p "$skills_dir"
            fi

            local duplicate_removed
            duplicate_removed=$(cleanup_duplicate_skill_links "$skills_dir")
            local log_head=""
            if [ "$duplicate_removed" -gt 0 ]; then
                log_head="  → [$dir_name] $project_name: 清理 $duplicate_removed 个重复技能 symlink"
                log "$log_head"
            fi

            # 仅在 --discover 时发现并 import 项目独有的技能（不在 categories/ 中的）
            if [ "$DO_DISCOVER" = true ] && [ "$dir_name" = ".claude" ]; then
                import_orphans "$skills_dir" "$project_name" "--scan-subdirs"
            fi

            # 第1步：清理目标目录下已不在 categories/ 中的孤立技能与旧副本
            for target_skill in "$skills_dir"/*; do
                [ -e "$target_skill" ] || [ -L "$target_skill" ] || continue
                local sname="$(basename "$target_skill")"
                [ "$sname" = ".system" ] && continue
                local in_repo=false
                for cat_dir in "$UNIVERSAL_SKILLS/categories"/*; do
                    if [ -d "$cat_dir/$sname" ]; then
                        in_repo=true
                        break
                    fi
                done
                if [ "$in_repo" = false ]; then
                    rm -rf "$target_skill"
                elif is_project_only_skill "$sname" && ! is_skill_allowed_for_project "$sname" "$project_dir"; then
                    rm -rf "$target_skill"
                elif [ -L "$target_skill" ]; then
                    rm -f "$target_skill"
                elif [ -d "$target_skill" ]; then
                    rm -rf "$target_skill"
                fi
            done

            # 清理旧分类目录（历史遗留）
            for category_dir in "$UNIVERSAL_SKILLS/categories"/*; do
                if [ -d "$category_dir" ]; then
                    local category_name="$(basename "$category_dir")"
                    if [ -d "$skills_dir/$category_name" ] && [ ! -L "$skills_dir/$category_name" ]; then
                        rm -rf "$skills_dir/$category_name"
                    fi
                fi
            done

            # 第2步：用实体文件同步技能（避免 git 追踪绝对路径 symlink 死链接）
            local skill_count=0
            local shared_skipped=0
            for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
                if is_syncable_skill_dir "$skill_dir"; then
                    local skill_name="$(basename "$skill_dir")"
                    # project-only 技能只同步到匹配的项目
                    if is_project_only_skill "$skill_name"; then
                        if ! is_skill_allowed_for_project "$skill_name" "$project_dir"; then
                            continue
                        fi
                    fi
                    # 项目级 .agents 去重：用户级已有则跳过（防 Codex USER+REPO 双条目）；
                    # 用户级缺失时仍拷贝兜底。第1步已清掉旧副本，不会残留。
                    if [ "$dir_name" = ".agents" ] && is_user_level_agent_skill "$skill_name"; then
                        shared_skipped=$((shared_skipped + 1))
                        continue
                    fi
                    local target="$skills_dir/$skill_name"
                    # 已存在非 symlink 的同名技能（marketplace/项目自有）- 跳过保护
                    if [ -e "$target" ] && [ ! -L "$target" ]; then
                        continue
                    fi
                    rm -f "$target" 2>/dev/null
                    cp -R "$skill_dir" "$target"
                    skill_count=$((skill_count + 1))
                fi
            done

            if [ $skill_count -gt 0 ] || [ $shared_skipped -gt 0 ]; then
                local skip_note=""
                [ $shared_skipped -gt 0 ] && skip_note="，跳过 $shared_skipped 个用户级已有（防 Codex 双条目）"
                log "  -> [$dir_name] $project_name: $skill_count 个技能 (实体文件)${skip_note}"
                any_done=true
                skill_count_total=$((skill_count_total + skill_count))
            fi
        done

        if $any_done; then
            synced_count=$((synced_count + 1))
        fi
    done

    if [ $synced_count -gt 0 ]; then
        success "已同步 $synced_count 个项目的 skills ($skill_count_total 个技能，实体文件，覆盖 .claude / .trae / .trae-cn / .agents)"
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

        # 清理旧的 .mdc 技能文件（也清理 project-only 不匹配项目的遗留文件）
        for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
            if is_syncable_skill_dir "$skill_dir"; then
                local skill_name="$(basename "$skill_dir")"
                if is_project_only_skill "$skill_name"; then
                    # 对不匹配的项目，确保清理掉遗留文件
                    if ! is_skill_allowed_for_project "$skill_name" "$project_dir"; then
                        rm -f "$cursor_rules_dir/$skill_name.mdc"
                        continue
                    fi
                fi
                rm -f "$cursor_rules_dir/$skill_name.mdc"
            fi
        done

        # 拷贝扁平化的技能并重命名为 .mdc 格式
        local skill_count=0
        for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
            if is_syncable_skill_dir "$skill_dir"; then
                local skill_name="$(basename "$skill_dir")"
                # project-only 技能只同步到匹配的项目
                if is_project_only_skill "$skill_name"; then
                    if ! is_skill_allowed_for_project "$skill_name" "$project_dir"; then
                        continue
                    fi
                fi
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

# 同步到 Cursor (.cursor/skills/)
# 现代 Cursor 支持 .cursor/skills/<skill>/SKILL.md 格式（替代旧的 .cursor/rules/*.mdc）。
# 与 sync_cursor_projects（.mdc，已废弃）不同，这里用逐技能同步（全局 symlink + 项目级实体文件）+ project-only 过滤。
# 同时同步全局 ~/.cursor/skills 与各项目 .cursor/skills，覆盖任意目录下的 Cursor 会话。
sync_cursor() {
    local synced_count=0
    local skill_count_total=0

    # 1) 全局 ~/.cursor/skills
    local global_target="$HOME/.cursor/skills"
    mkdir -p "$global_target"
    local g_count=0
    # 清理全局 ~/.cursor/skills 中的死链接与已删除技能
    for entry in "$global_target"/*; do
        [ -e "$entry" ] || [ -L "$entry" ] || continue
        local sname="$(basename "$entry")"
        [ "$sname" = ".system" ] && continue
        local in_repo=false
        for cat_dir in "$UNIVERSAL_SKILLS/categories"/*; do
            if [ -d "$cat_dir/$sname" ]; then
                in_repo=true
                break
            fi
        done
        if [ "$in_repo" = false ] || [ ! -e "$entry" ]; then
            rm -rf "$entry"
        fi
    done

    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            if is_project_only_skill "$skill_name"; then
                continue
            fi
            local link="$global_target/$skill_name"
            if [ -L "$link" ]; then
                rm -f "$link"
            elif [ -e "$link" ]; then
                continue
            fi
            ln -sfh "$skill_dir" "$link"
            g_count=$((g_count + 1))
        fi
    done
    if [ $g_count -gt 0 ]; then
        log "  → ~/.cursor/skills (全局): $g_count 个技能"
        synced_count=$((synced_count + 1))
        skill_count_total=$((skill_count_total + g_count))
    fi

    # 2) 项目级 .cursor/skills（仅对已存在 .cursor 目录的项目）
    if [ -z "${unique_projects+x}" ]; then
        discover_projects
    fi

    for project_dir in "${unique_projects[@]}"; do
        local project_name="$(basename "$project_dir")"
        if [ ! -d "$project_dir/.cursor" ]; then
            continue
        fi
        local skills_dir="$project_dir/.cursor/skills"
        mkdir -p "$skills_dir"

        # 清理旧 .mdc 遗留（以前 sync_cursor_projects 写的）
        rm -f "$project_dir/.cursor/rules/"*.mdc 2>/dev/null || true

        # 清理已不在 categories/ 中的孤立技能与旧拷贝
        for target_skill in "$skills_dir"/*; do
            [ -e "$target_skill" ] || [ -L "$target_skill" ] || continue
            local sname="$(basename "$target_skill")"
            [ "$sname" = ".system" ] && continue
            local in_repo=false
            for cat_dir in "$UNIVERSAL_SKILLS/categories"/*; do
                if [ -d "$cat_dir/$sname" ]; then
                    in_repo=true
                    break
                fi
            done
            if [ "$in_repo" = false ]; then
                rm -rf "$target_skill"
            elif is_project_only_skill "$sname" && ! is_skill_allowed_for_project "$sname" "$project_dir"; then
                rm -rf "$target_skill"
            elif [ -d "$target_skill" ] && [ ! -L "$target_skill" ]; then
                rm -rf "$target_skill"
            fi
        done

        # 用 symlink 同步技能
        local skill_count=0
        for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
            if is_syncable_skill_dir "$skill_dir"; then
                local skill_name="$(basename "$skill_dir")"
                if is_project_only_skill "$skill_name"; then
                    if ! is_skill_allowed_for_project "$skill_name" "$project_dir"; then
                        continue
                    fi
                fi
                local target="$skills_dir/$skill_name"
                if [ -e "$target" ] && [ ! -L "$target" ]; then
                    continue
                fi
                rm -f "$target" 2>/dev/null
                cp -R "$skill_dir" "$target"
                skill_count=$((skill_count + 1))
            fi
        done

        if [ $skill_count -gt 0 ]; then
            log "  → $project_name (.cursor/skills): $skill_count 个技能"
            synced_count=$((synced_count + 1))
            skill_count_total=$((skill_count_total + skill_count))
        fi
    done

    if [ $synced_count -gt 0 ]; then
        success "已同步 Cursor skills ($skill_count_total 个技能，全局 symlink + 项目级实体文件)"
    fi
}

# 同步到 Codex
sync_codex() {
    local target="$HOME/.codex/skills"

    if [ ! -d "$HOME/.codex" ]; then
        return
    fi

    # 仅在 --discover 时扫描孤立技能
    if [ "$DO_DISCOVER" = true ]; then
        import_orphans "$target" "Codex"
    fi

    if [ -d "$target" ] && [ ! -L "$target" ]; then
        backup "$target"
    fi

    # 增量同步：绝不 rm -rf 整个目标目录。
    # Codex 会自愈 ~/.codex/skills/.system/ 内置技能（marker: .codex-system-skills.marker），
    # rm 过程中 .system 被并发重建会导致 rm 报错 + set -e 中断，目标被清空（2026-09-10 实测）。
    # 只管理我们创建的 symlink：补缺失、更新指向、删孤立；点文件与实体原样保留。
    mkdir -p "$target"
    prune_shared_duplicates "$target" "Codex"

    local skill_count=0
    local shared_skipped=0
    local wanted_list
    wanted_list="$(mktemp)"

    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            # 全局同步：跳过项目专用技能
            if is_project_only_skill "$skill_name"; then
                continue
            fi
            if is_shared_agent_skill "$skill_name"; then
                shared_skipped=$((shared_skipped + 1))
                continue
            fi
            # -h：目标若是已存在的目录 symlink，必须替换链接本身；
            # 裸 -sf 会解引用，在被指目录内建 D/N 嵌套链接（含自环），且原链接永远不更新
            ln -sfh "$skill_dir" "$target/$skill_name"
            echo "$skill_name" >> "$wanted_list"
            skill_count=$((skill_count + 1))
        fi
    done

    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            if is_shared_agent_skill "$skill_name"; then
                shared_skipped=$((shared_skipped + 1))
                continue
            fi
            if [ ! -d "$target/$skill_name" ] && [ ! -L "$target/$skill_name" ]; then
                ln -sfh "$skill_dir" "$target/$skill_name"
                echo "$skill_name" >> "$wanted_list"
                skill_count=$((skill_count + 1))
            fi
        fi
    done

    # 清理孤立 symlink：仅删非点文件、且不在本轮清单中的 symlink；
    # `$target/*` 不展开点文件，.system 等 Codex 自有内容天然跳过。
    for entry in "$target"/*; do
        [ -L "$entry" ] || continue
        local entry_name
        entry_name="$(basename "$entry")"
        local entry_dest
        entry_dest="$(readlink "$entry" 2>/dev/null || true)"
        if [[ "$entry_dest" == "$UNIVERSAL_SKILLS/categories/"* ]] && \
           ! grep -qx "$entry_name" "$wanted_list" 2>/dev/null; then
            rm -f "$entry"
        fi
    done
    rm -f "$wanted_list"

    success "Codex skills 已同步 ($skill_count 个独占 symlink，跳过 $shared_skipped 个 ~/.agents/skills/ 已提供技能)"
}

# 同步到 ZCode (~/.agents/skills/)
# ZCode 在 ~/.agents/skills/ 下管理技能，含 .skill-lock.json 锁定的 well-known
# 技能（lark-*）和内置技能（gstack/autoplan 等）。必须增量同步，不得 rm -rf。
sync_zcode() {
    local target="$HOME/.agents/skills"

    if [ ! -d "$HOME/.agents" ]; then
        return
    fi

    mkdir -p "$target"
    local duplicate_removed
    duplicate_removed=$(cleanup_duplicate_skill_links "$target")
    # 清理指向 universal-skills 但源已不存在的死链接
    local dead_removed=0
    for entry in "$target"/*; do
        [ -e "$entry" ] || [ -L "$entry" ] || continue
        if [ -L "$entry" ]; then
            local dest="$(readlink "$entry" 2>/dev/null || true)"
            if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]] && [ ! -e "$dest" ]; then
                rm -f "$entry"
                dead_removed=$((dead_removed + 1))
            fi
        fi
    done
    [ "$dead_removed" -gt 0 ] && log "  清理 ZCode $dead_removed 个死 symlink（源已不存在）"

    # 注意：不要对 ~/.agents/skills/ 调用 import_orphans。
    # 该目录由 ZCode 管理，含大量内置/well-known 技能（lark-*, gstack, autoplan 等），
    # import_orphans 会把它们误判为孤立技能并 cp -r 到 categories/imported/，造成污染。

    # 增量同步：只处理 universal-skills 的技能，绝不删除其他技能
    local skill_count=0
    local skipped=0
    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            # 全局同步：跳过项目专用技能，同时清理以前创建的遗留 symlink
            if is_project_only_skill "$skill_name"; then
                local link="$target/$skill_name"
                if [ -L "$link" ]; then
                    local dest
                    dest="$(readlink "$link")"
                    if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                        rm -f "$link"
                    fi
                fi
                continue
            fi
            local link="$target/$skill_name"

            # 已是指向同一目标的 symlink → 跳过
            if [ -L "$link" ] && [ "$(readlink "$link")" = "$skill_dir" ]; then
                continue
            fi

            # 已存在且非我们管理的 symlink（内置/well-known/项目自有） → 跳过
            if [ -e "$link" ] || [ -L "$link" ]; then
                skipped=$((skipped + 1))
                continue
            fi

            ln -sfh "$skill_dir" "$link"
            skill_count=$((skill_count + 1))
        fi
    done

    if [ $skill_count -gt 0 ]; then
        success "ZCode skills 已同步 ($skill_count 个技能，增量 symlink)"
        [ $skipped -gt 0 ] && warn "  跳过 $skipped 个已存在的非 universal-skills 技能（保护内置/well-known）"
    else
        log "ZCode skills 无需更新（全部已同步）"
    fi
    log "  路径: ~/.agents/skills/"

    if [ -d "$HOME/.zcode/skills" ]; then
        local legacy_target="$HOME/.zcode/skills"
        local legacy_removed=0
        local legacy_duplicate_removed
        legacy_duplicate_removed=$(cleanup_duplicate_skill_links "$legacy_target")

        # ZCode/Agent 现在会同时看到 ~/.agents/skills 和 ~/.zcode/skills。
        # 为避免同一 universal skill 出现两份，只清理我们以前创建的 legacy symlink，
        # 不再往 ~/.zcode/skills 写入新的 universal-skills 链接。
        for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/* "$UNIVERSAL_SKILLS/categories"/*; do
            if is_syncable_skill_dir "$skill_dir"; then
                local skill_name="$(basename "$skill_dir")"
                local link="$legacy_target/$skill_name"

                if [ -L "$link" ]; then
                    rm -f "$link"
                    legacy_removed=$((legacy_removed + 1))
                fi
            fi
        done

        legacy_removed=$((legacy_removed + legacy_duplicate_removed))
        if [ $legacy_removed -gt 0 ]; then
            success "ZCode legacy duplicate symlinks 已清理 ($legacy_removed 个)"
        else
            log "ZCode legacy skills 无 universal-skills 重复 symlink"
        fi
        log "  legacy 路径: ~/.zcode/skills/ (不再同步 universal skills)"
    fi
}

# 同步到 Grok Build (~/.grok/skills/)
# Grok 从 ~/.grok/skills/ 加载用户级技能（同时也会读取 ~/.claude/skills/ 作兼容）。
# 这里显式增量 symlink，保证不依赖 Claude 兼容开关即可注册。
sync_grok() {
    local target="$HOME/.grok/skills"

    if [ ! -d "$HOME/.grok" ]; then
        return
    fi

    mkdir -p "$target"
    cleanup_dead_universal_links "$target"
    local duplicate_removed
    duplicate_removed=$(cleanup_duplicate_skill_links "$target")
    [ "$duplicate_removed" -gt 0 ] && log "  清理 Grok 重复技能 symlink: $duplicate_removed 个"

    local skill_count=0
    local skipped=0
    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            # 全局同步：跳过项目专用技能，清理遗留 symlink
            if is_project_only_skill "$skill_name"; then
                local link="$target/$skill_name"
                if [ -L "$link" ]; then
                    local dest
                    dest="$(readlink "$link")"
                    if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                        rm -f "$link"
                    fi
                fi
                continue
            fi
            local link="$target/$skill_name"

            # 已是指向同一目标的 symlink → 跳过
            if [ -L "$link" ] && [ "$(readlink "$link")" = "$skill_dir" ]; then
                continue
            fi

            # 如果是指向 universal-skills 的旧 symlink，清理以便重建
            if [ -L "$link" ]; then
                local dest
                dest="$(readlink "$link")"
                if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                    rm -f "$link"
                fi
            fi

            # 已存在且非我们管理的技能（Grok bundled/plugin/用户自有） → 跳过
            if [ -e "$link" ] || [ -L "$link" ]; then
                skipped=$((skipped + 1))
                continue
            fi

            ln -sfh "$skill_dir" "$link"
            skill_count=$((skill_count + 1))
        fi
    done

    if [ $skill_count -gt 0 ]; then
        success "Grok Build skills 已同步 ($skill_count 个技能，增量 symlink)"
        [ $skipped -gt 0 ] && warn "  跳过 $skipped 个已存在的非 universal-skills 技能"
    else
        log "Grok Build skills 无需更新（全部已同步）"
    fi
    log "  路径: ~/.grok/skills/"
}

# 同步到 Qoder (~/.qoder/skills/，~/.qoder 是指向 ~/.qoder-cn 的 symlink)
# qoder-cn 会同时加载 ~/.qoder/skills/ 和 ~/.agents/skills/ 两个用户级入口，
# 同名技能触发 "overrides same-source skill" 告警。因此已被 ~/.agents/skills/
# 覆盖的技能不再重复注册（与 Codex 策略一致），只补共享入口缺失的部分。
sync_qoder() {
    local target="$HOME/.qoder/skills"

    if [ ! -d "$HOME/.qoder" ]; then
        return
    fi

    mkdir -p "$target"
    cleanup_dead_universal_links "$target"
    local duplicate_removed
    duplicate_removed=$(cleanup_duplicate_skill_links "$target")
    [ "$duplicate_removed" -gt 0 ] && log "  清理 Qoder 重复技能 symlink: $duplicate_removed 个"
    prune_shared_duplicates "$target" "Qoder"

    local skill_count=0
    local skipped=0
    local shared_skipped=0
    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            # 全局同步：跳过项目专用技能，清理遗留 symlink
            if is_project_only_skill "$skill_name"; then
                local link="$target/$skill_name"
                if [ -L "$link" ]; then
                    local dest
                    dest="$(readlink "$link")"
                    if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                        rm -f "$link"
                    fi
                fi
                continue
            fi
            # ~/.agents/skills/ 已提供同名技能 → 不重复注册（避免 qoder-cn 双入口告警）
            if is_shared_agent_skill "$skill_name"; then
                shared_skipped=$((shared_skipped + 1))
                continue
            fi
            local link="$target/$skill_name"

            # 已是指向同一目标的 symlink → 跳过
            if [ -L "$link" ] && [ "$(readlink "$link")" = "$skill_dir" ]; then
                continue
            fi

            # 如果是指向 universal-skills 的旧 symlink，清理以便重建
            if [ -L "$link" ]; then
                local dest
                dest="$(readlink "$link")"
                if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                    rm -f "$link"
                fi
            fi

            # 已存在且非我们管理的技能（Qoder bundled/plugin/用户自有） → 跳过
            if [ -e "$link" ] || [ -L "$link" ]; then
                skipped=$((skipped + 1))
                continue
            fi

            ln -sfh "$skill_dir" "$link"
            skill_count=$((skill_count + 1))
        fi
    done

    if [ $skill_count -gt 0 ]; then
        success "Qoder skills 已同步 ($skill_count 个技能，增量 symlink)"
        [ $skipped -gt 0 ] && warn "  跳过 $skipped 个已存在的非 universal-skills 技能"
    else
        log "Qoder skills 无需更新（全部已同步）"
    fi
    [ $shared_skipped -gt 0 ] && log "  跳过 $shared_skipped 个 ~/.agents/skills/ 已提供技能（双入口去重）"
    log "  路径: ~/.qoder/skills/"
}

# 同步到 OpenCode (~/.config/opencode/skills/)
# OpenCode 从 ~/.config/opencode/skills/ 加载全局技能，
# 同时也兼容读取 ~/.claude/skills/ 和 ~/.agents/skills/。
# 这里显式增量 symlink，保证不依赖兼容层即可注册。
sync_opencode() {
    local target="$HOME/.config/opencode/skills"

    if [ ! -d "$HOME/.config/opencode" ]; then
        return
    fi

    mkdir -p "$target"
    cleanup_dead_universal_links "$target"
    local duplicate_removed
    duplicate_removed=$(cleanup_duplicate_skill_links "$target")
    [ "$duplicate_removed" -gt 0 ] && log "  清理 OpenCode 重复技能 symlink: $duplicate_removed 个"

    local skill_count=0
    local skipped=0
    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            # 全局同步：跳过项目专用技能，清理遗留 symlink
            if is_project_only_skill "$skill_name"; then
                local link="$target/$skill_name"
                if [ -L "$link" ]; then
                    local dest
                    dest="$(readlink "$link")"
                    if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                        rm -f "$link"
                    fi
                fi
                continue
            fi
            local link="$target/$skill_name"

            # 已是指向同一目标的 symlink -> 跳过
            if [ -L "$link" ] && [ "$(readlink "$link")" = "$skill_dir" ]; then
                continue
            fi

            # 如果是指向 universal-skills 的旧 symlink，清理以便重建
            if [ -L "$link" ]; then
                local dest
                dest="$(readlink "$link")"
                if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                    rm -f "$link"
                fi
            fi

            # 已存在且非我们管理的技能（OpenCode plugin/builtin/用户自有） -> 跳过
            if [ -e "$link" ] || [ -L "$link" ]; then
                skipped=$((skipped + 1))
                continue
            fi

            ln -sfh "$skill_dir" "$link"
            skill_count=$((skill_count + 1))
        fi
    done

    if [ $skill_count -gt 0 ]; then
        success "OpenCode skills 已同步 ($skill_count 个技能，增量 symlink)"
        [ $skipped -gt 0 ] && warn "  跳过 $skipped 个已存在的非 universal-skills 技能"
    else
        log "OpenCode skills 无需更新（全部已同步）"
    fi
    log "  路径: ~/.config/opencode/skills/"
}

# 同步到 PI Agent (~/.pi/agent/skills/)
# PI 会同时加载 ~/.pi/agent/skills/ 与 ~/.agents/skills/ 两个 user 级入口
# （pi 0.85 loadSkills：userDirs.skills + userAgentsSkillsDir）。
# 两处同名技能会在宿主侧报 "name <x> collision" 告警噪声，
# 因此 ~/.agents/skills/ 已提供的技能不再在 PI 目录重复注册。
sync_pi() {
    local target="$HOME/.pi/agent/skills"

    if [ ! -d "$HOME/.pi" ]; then
        return
    fi

    mkdir -p "$target"
    cleanup_dead_universal_links "$target"
    local duplicate_removed
    duplicate_removed=$(cleanup_duplicate_skill_links "$target")
    [ "$duplicate_removed" -gt 0 ] && log "  清理 PI Agent 重复技能 symlink: $duplicate_removed 个"
    prune_shared_duplicates "$target" "PI Agent"

    local skill_count=0
    local skipped=0
    local shared_skipped=0
    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            # ~/.agents/skills/ 已提供同名技能 -> 不重复注册（避免 PI 双入口 collision）
            if is_shared_agent_skill "$skill_name"; then
                shared_skipped=$((shared_skipped + 1))
                continue
            fi
            # 全局同步：跳过项目专用技能，清理遗留 symlink
            if is_project_only_skill "$skill_name"; then
                local link="$target/$skill_name"
                if [ -L "$link" ]; then
                    local dest
                    dest="$(readlink "$link")"
                    if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                        rm -f "$link"
                    fi
                fi
                continue
            fi
            local link="$target/$skill_name"

            # 已是指向同一目标的 symlink -> 跳过
            if [ -L "$link" ] && [ "$(readlink "$link")" = "$skill_dir" ]; then
                continue
            fi

            # 如果是指向 universal-skills 的旧 symlink，清理以便重建
            if [ -L "$link" ]; then
                local dest
                dest="$(readlink "$link")"
                if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                    rm -f "$link"
                fi
            fi

            # 已存在且非我们管理的技能（PI builtin/用户自有） -> 跳过
            if [ -e "$link" ] || [ -L "$link" ]; then
                skipped=$((skipped + 1))
                continue
            fi

            ln -sfh "$skill_dir" "$link"
            skill_count=$((skill_count + 1))
        fi
    done

    if [ $skill_count -gt 0 ]; then
        success "PI Agent skills 已同步 ($skill_count 个独占 symlink，跳过 $shared_skipped 个 ~/.agents/skills/ 已提供技能)"
        [ $skipped -gt 0 ] && warn "  跳过 $skipped 个已存在的非 universal-skills 技能"
    else
        log "PI Agent skills 无需更新（$shared_skipped 个技能由 ~/.agents/skills/ 提供）"
    fi
    log "  路径: ~/.pi/agent/skills/"
}

# 同步到 Trae CN Agent (~/.trae-cn/skills/) 和 Trae Work (~/.trae/skills/)
# 两者都管理 Agent skills，含 marketplace/builtin 技能。
# 必须增量同步，不得 rm -rf，避免覆盖 Trae 自带或已安装的 marketplace 技能。
sync_trae_cn() {
    local trae_dirs=("$HOME/.trae-cn" "$HOME/.trae")

    for trae_home in "${trae_dirs[@]}"; do
        if [ ! -d "$trae_home" ]; then
            continue
        fi

        local target="$trae_home/skills"
        local label="$(basename "$trae_home")"

        # TraeCode (TRAE SOLO CN, ~/.trae-cn) 无法解析 symlink，必须用真实副本；
        # TraeWork (~/.trae) 可解析 symlink，走零磁盘 symlink。
        local use_real_copy=false
        [[ "$label" == ".trae-cn" ]] && use_real_copy=true

        mkdir -p "$target"

        # TraeCode 用真实副本：若残留指向 universal-skills 但源已不存在的死 symlink，自动清理
        if [ "$use_real_copy" = true ]; then
            local dead_removed=0
            local item dest
            for item in "$target"/*; do
                if [ -L "$item" ]; then
                    dest="$(readlink "$item")"
                    if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]] && [ ! -e "$dest" ]; then
                        rm -f "$item"
                        dead_removed=$((dead_removed + 1))
                    fi
                fi
            done
            [ "$dead_removed" -gt 0 ] && log "  清理 $dead_removed 个死 symlink（源已不存在）"
        fi

        local duplicate_removed
        duplicate_removed=$(cleanup_duplicate_skill_links "$target")
        [ "$duplicate_removed" -gt 0 ] && log "  清理 $label 重复技能 symlink: $duplicate_removed 个"

        local skill_count=0
        local refreshed=0
        local skipped=0
        for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
            if is_syncable_skill_dir "$skill_dir"; then
                local skill_name="$(basename "$skill_dir")"
                # 全局同步：跳过项目专用技能，清理遗留 symlink / 旧 copy
                if is_project_only_skill "$skill_name"; then
                    local link="$target/$skill_name"
                    if [ -L "$link" ]; then
                        rm -f "$link"
                        refreshed=$((refreshed + 1))
                    elif [ -d "$link" ] && [ -f "$link/SKILL.md" ]; then
                        # 我们自己的 project-only 技能曾经被 copy 过（非 symlink 模式），
                        # 含 SKILL.md 可以确认不是 Trae marketplace 内置（它们通常不同名）
                        rm -rf "$link"
                        refreshed=$((refreshed + 1))
                    fi
                    continue
                fi
                local link="$target/$skill_name"

                if [ "$use_real_copy" = true ]; then
                    # TraeCode 无法解析 symlink，用真实副本
                    if [ -L "$link" ]; then
                        rm -f "$link"
                        refreshed=$((refreshed + 1))
                    elif [ -e "$link" ]; then
                        # 已存在非 symlink（marketplace 或旧副本），跳过保护
                        skipped=$((skipped + 1))
                        continue
                    fi
                    cp -R "$skill_dir" "$link"
                else
                    # TraeWork 可解析 symlink，走零磁盘 symlink
                    if [ -L "$link" ]; then
                        rm -f "$link"
                        refreshed=$((refreshed + 1))
                    elif [ -e "$link" ]; then
                        skipped=$((skipped + 1))
                        continue
                    fi
                    ln -sfh "$skill_dir" "$link"
                fi
                skill_count=$((skill_count + 1))
            fi
        done

        if [ "$use_real_copy" = true ]; then
            success "$label skills 已同步 ($skill_count 个技能，真实副本)"
        else
            success "$label skills 已同步 ($skill_count 个技能，增量 symlink)"
        fi
        [ $refreshed -gt 0 ] && log "  刷新 $refreshed 个已有 symlink"
        [ $skipped -gt 0 ] && warn "  跳过 $skipped 个已存在的非 symlink 技能（保护 marketplace/builtin）"
        log "  路径: $target/"
    done
}

# 同步到 Kimi Code (~/.kimi-code/skills/)
# Kimi Code 通过 config.toml 的 extra_skill_dirs 加载技能，并用
# merge_all_available_skills = true 合并。需建扁平 skills 目录并注册。
sync_kimi_code() {
    local target="$HOME/.kimi-code/skills"
    local config="$HOME/.kimi-code/config.toml"

    if [ ! -d "$HOME/.kimi-code" ]; then
        return
    fi

    mkdir -p "$target"
    cleanup_dead_universal_links "$target"
    local duplicate_removed
    duplicate_removed=$(cleanup_duplicate_skill_links "$target")
    [ "$duplicate_removed" -gt 0 ] && log "  清理 Kimi Code 重复技能 symlink: $duplicate_removed 个"

    # 清理旧的 universal-skills symlink 后重建（目录为我们所有，安全）
    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            # 全局同步：跳过项目专用技能，清理遗留 symlink
            if is_project_only_skill "$skill_name"; then
                local link="$target/$skill_name"
                if [ -L "$link" ]; then
                    rm -f "$link"
                fi
                continue
            fi
            local link="$target/$skill_name"
            if [ -L "$link" ]; then
                rm -f "$link"
            elif [ -e "$link" ]; then
                # 非 symlink 的同名内容，跳过避免覆盖
                continue
            fi
            ln -sfh "$skill_dir" "$link"
        fi
    done

    # 注册到 config.toml 的 extra_skill_dirs
    if [ -f "$config" ]; then
        register_extra_skill_dir "$config" "$target"
    fi

    local skill_count
    skill_count=$(find "$target" -maxdepth 1 -type l 2>/dev/null | wc -l | tr -d ' ')

    success "Kimi Code skills 已同步 ($skill_count 个技能，symlink)"
    log "  路径: ~/.kimi-code/skills/ (已注册到 config.toml extra_skill_dirs)"
}

# 同步统一开发流程 (unified-dev-flow) 物理门禁钩子到宿主环境与 Git 项目
sync_workflow_hooks() {
    log "同步统一开发流程 (unified-dev-flow) 门禁钩子..."

    local scripts_src="$UNIVERSAL_SKILLS/categories/workflow/unified-dev-flow/scripts"
    local claude_scripts="$HOME/.claude/scripts"

    mkdir -p "$claude_scripts"

    # 1. 拷贝最新门禁脚本并赋权
    cp -f "$scripts_src/entry-gate-check.py" "$claude_scripts/entry-gate-check.py"
    cp -f "$scripts_src/entry-gate-antigravity.py" "$claude_scripts/entry-gate-antigravity.py"
    cp -f "$scripts_src/git-pre-push-guard.sh" "$claude_scripts/git-pre-push-guard.sh"
    chmod +x "$claude_scripts/entry-gate-check.py" "$claude_scripts/entry-gate-antigravity.py" "$claude_scripts/git-pre-push-guard.sh"
    success "已同步最新门禁脚本到 $claude_scripts"

    # 2. 配置 Claude Code (~/.claude/settings.json)
    python3 - <<'EOF'
import json, os

settings_path = os.path.expanduser("~/.claude/settings.json")
try:
    if os.path.isfile(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
except Exception:
    data = {}

hooks = data.setdefault("hooks", {})

# PreToolUse
pre = hooks.setdefault("PreToolUse", [])
has_entry = any("entry-gate-check.py" in str(h) for h in pre)
if not has_entry:
    pre.append({
        "matcher": "Edit|Write",
        "hooks": [{
            "command": "python3 ~/.claude/scripts/entry-gate-check.py",
            "timeout": 10000,
            "type": "command"
        }]
    })

# Stop (enforce review check)
stop = hooks.setdefault("Stop", [])
has_stop_review = any("check-review" in str(h) for h in stop)
if not has_stop_review:
    stop.append({
        "hooks": [{
            "command": "python3 ~/.claude/scripts/entry-gate-check.py --check-review",
            "timeout": 15000,
            "type": "command"
        }]
    })

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
with open(settings_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
EOF
    success "已配置 Claude Code 门禁 (~/.claude/settings.json: PreToolUse + Stop check-review)"

    # 3. 配置 Codex CLI (~/.codex/hooks.json)
    python3 - <<'EOF'
import json, os

hooks_path = os.path.expanduser("~/.codex/hooks.json")
try:
    if os.path.isfile(hooks_path):
        with open(hooks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
except Exception:
    data = {}

hooks = data.setdefault("hooks", {})

# PreToolUse
pre = hooks.setdefault("PreToolUse", [])
has_entry = any("entry-gate-check.py" in str(h) for h in pre)
if not has_entry:
    pre.append({
        "matcher": "Edit|Write|apply_patch",
        "hooks": [{
            "command": "python3 ~/.claude/scripts/entry-gate-check.py",
            "timeout": 10,
            "type": "command"
        }]
    })

# Stop
stop = hooks.setdefault("Stop", [])
has_stop_review = any("check-review" in str(h) for h in stop)
if not has_stop_review:
    stop.append({
        "hooks": [{
            "command": "python3 ~/.claude/scripts/entry-gate-check.py --check-review",
            "timeout": 15,
            "type": "command"
        }]
    })

os.makedirs(os.path.dirname(hooks_path), exist_ok=True)
with open(hooks_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
EOF
    success "已配置 Codex CLI 门禁 (~/.codex/hooks.json: PreToolUse + Stop check-review)"

    # 4. 配置 Antigravity / Gemini CLI (~/.gemini/config/hooks.json)
    python3 - <<'EOF'
import json, os

hooks_path = os.path.expanduser("~/.gemini/config/hooks.json")
try:
    if os.path.isfile(hooks_path):
        with open(hooks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
except Exception:
    data = {}

# entry-gate PreToolUse
data["entry-gate"] = {
    "PreToolUse": [{
        "matcher": "code_action|write_to_file|replace_file_content",
        "hooks": [{
            "command": "python3 ~/.claude/scripts/entry-gate-antigravity.py",
            "timeout": 10,
            "type": "command"
        }]
    }]
}

# entry-gate-stop Stop hook (Flat structure: Stop is a list of handler objects directly)
data["entry-gate-stop"] = {
    "Stop": [{
        "command": "python3 ~/.claude/scripts/entry-gate-antigravity.py --stop",
        "timeout": 30,
        "type": "command"
    }]
}

os.makedirs(os.path.dirname(hooks_path), exist_ok=True)
with open(hooks_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
EOF
    success "已配置 Antigravity / Gemini CLI 门禁 (~/.gemini/config/hooks.json)"

    # 5. 为全量已知 Git 仓库及 worktree 安装 pre-push 物理门禁
    local target_repos=(
        "$HOME/clawd"
        "$HOME/clawd-work"
        "$HOME/nexusarchive"
        "$HOME/everything-claude-code"
        "$HOME/JLAF"
        "$HOME/PLM"
        "$HOME/zhitoujianli"
        "$HOME/liujie"
        "$HOME/mimo"
        "$HOME/xiyu/xiyu-bid-poc"
        "$UNIVERSAL_SKILLS"
    )
    if [ -d "$HOME/xiyu/worktrees" ]; then
        while IFS= read -r -d '' wt; do
            target_repos+=("$wt")
        done < <(find "$HOME/xiyu/worktrees" -maxdepth 1 -mindepth 1 -type d -print0 2>/dev/null)
    fi

    for repo in "${target_repos[@]}"; do
        if [ -d "$repo/.git" ] || [ -f "$repo/.git" ]; then
            local hook_dir
            hook_dir="$(git -C "$repo" rev-parse --git-path hooks 2>/dev/null || echo "")"
            if [ -n "$hook_dir" ]; then
                if [[ "$hook_dir" != /* ]]; then
                    hook_dir="$repo/$hook_dir"
                fi
                mkdir -p "$hook_dir"
                local pre_push="$hook_dir/pre-push"
                cp -f "$claude_scripts/git-pre-push-guard.sh" "$pre_push"
                chmod +x "$pre_push"
                success "已安装 Git pre-push 门禁: $repo -> $pre_push"
            fi
        fi
    done
}

# 刷新 SKILLS-INDEX.md 技能速查表（每次同步后自动更新）
update_skills_index() {
    local script="$UNIVERSAL_SKILLS/scripts/generate-skills-index.py"
    if [ ! -f "$script" ]; then
        warn "SKILLS-INDEX 生成脚本缺失: $script（跳过索引刷新）"
        return 0
    fi
    if python3 "$script" > /dev/null 2>&1; then
        success "SKILLS-INDEX.md 技能索引已刷新"
    else
        warn "SKILLS-INDEX.md 索引刷新失败（见上述脚本输出）"
    fi
}

# 同步到项目级 skills（为 Gemini/Gemini in projects）
# 注意：不再使用 categories/ 整目录 symlink，改为逐技能创建扁平 symlink，
# 以便精确过滤 project-only 技能（如 xiyu-server-deploy 只能在 xiyu* 项目中出现）。
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
        "$HOME/mimo"
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

        # 目标目录：$skills_dir/universal-skills（真实目录，内部放实体文件，非 symlink）
        local target_dir="$skills_dir/universal-skills"

        # 清理旧的整目录 symlink（以前指向 $UNIVERSAL_SKILLS/categories）
        if [ -L "$target_dir" ]; then
            rm -f "$target_dir"
        elif [ -d "$target_dir" ]; then
            # 已是目录：
            # 1) 清掉最大深度 1 下指向我们 categories 的旧 symlink（扁平模式遗留）
            find "$target_dir" -maxdepth 1 -type l -print0 2>/dev/null | while IFS= read -r -d '' l; do
                dest=$(readlink "$l" 2>/dev/null || true)
                if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                    rm -f "$l"
                fi
            done
            # 2) 清理 project-only 技能的任何残留（即使嵌套在 deployment/... 等分类子目录里）
            for entry in "${PROJECT_ONLY_SKILLS[@]}"; do
                s_name="${entry%%:*}"
                if ! is_skill_allowed_for_project "$s_name" "$project_dir"; then
                    # 递归查找此项目 universal-skills 下所有名为 $s_name 的目录/symlink 并删除
                    find "$target_dir" -maxdepth 5 \( -type d -o -type l \) -name "$s_name" -print0 2>/dev/null | while IFS= read -r -d '' p; do
                        if [ -L "$p" ]; then
                            rm -f "$p"
                        elif [ -d "$p" ]; then
                            rm -rf "$p"
                        fi
                    done
                fi
            done
            # 3) 清理空的分类目录（deployment / coding 等如果空了）
            find "$target_dir" -mindepth 1 -maxdepth 1 -type d -empty -print0 2>/dev/null | while IFS= read -r -d '' d; do
                rmdir "$d" 2>/dev/null || true
            done
            # 4) 清理已从 categories 删除的过期技能副本（历史删除自动传播）
            local known_list
            local orphan_removed=0
            known_list=$(find "$UNIVERSAL_SKILLS/categories" -mindepth 2 -maxdepth 2 -type f -name "SKILL.md" -exec dirname {} \; 2>/dev/null | while IFS= read -r p; do basename "$p"; done | sort)
            for p in "$target_dir"/*; do
                [ -e "$p" ] || [ -L "$p" ] || continue
                if ! printf '%s\n' "$known_list" | grep -qx "$(basename "$p")"; then
                    rm -rf "$p"
                    orphan_removed=$((orphan_removed + 1))
                fi
            done
            [ "$orphan_removed" -gt 0 ] && log "  清理 $orphan_removed 个已删除技能的过期副本"
        fi

        mkdir -p "$target_dir"

        # 逐技能增量复制实体文件（diff 校验：仅漂移技能重拷，幂等可重试），过滤 project-only
        local skill_count=0
        local unchanged_count=0
        for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
            if is_syncable_skill_dir "$skill_dir"; then
                local skill_name="$(basename "$skill_dir")"
                # project-only 技能只同步到匹配的项目
                if is_project_only_skill "$skill_name"; then
                    if ! is_skill_allowed_for_project "$skill_name" "$project_dir"; then
                        continue
                    fi
                fi
                if sync_skill_copy "$skill_dir" "$target_dir/$skill_name"; then
                    skill_count=$((skill_count + 1))
                else
                    unchanged_count=$((unchanged_count + 1))
                fi
            fi
        done

        if [ "$skill_count" -gt 0 ] || [ "$unchanged_count" -gt 0 ]; then
            # bash 3.2 在 C.UTF-8 下展开「ASCII数字直接接全角标点」（如 $skill_count，）
            # 会丢失数字与标点首字节，故数字与全角逗号间保留空格
            log "✓ $project_name: universal-skills 校验完成 (更新 $skill_count ，一致 $unchanged_count)"
            synced_count=$((synced_count + 1))
        fi
    done

    if [ $synced_count -gt 0 ]; then
        success "已同步 $synced_count 个项目的 universal-skills（project-only 过滤）"
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

    # 1. 自动从 categories/ 重建 GEMINI.md 全量技能表
    if [ -f "$UNIVERSAL_SKILLS/scripts/generate-gemini-md.py" ]; then
        python3 "$UNIVERSAL_SKILLS/scripts/generate-gemini-md.py" >/dev/null 2>&1 \
            && log "  Antigravity: GEMINI.md 已从 categories/ 自动重建" \
            || warn "Antigravity: GEMINI.md 自动重建失败"
    fi

    # 2. 检查 GEMINI.md 是否存在
    if [ ! -f "$extension_src/GEMINI.md" ]; then
        warn "Antigravity: GEMINI.md 缺失于 $extension_src"
        return 1
    fi

    # 3. 检查 extension 是否已安装（symlink 到源目录）
    if [ ! -d "$extension_install" ]; then
        warn "Antigravity: universal-skills extension 未安装"
        warn "  请运行: gemini extensions link \"$extension_src\""
        return 1
    fi

    # 4. 检查 extension 是否为 symlink（链接式安装）
    local install_json="$extension_install/.gemini-extension-install.json"
    if [ -f "$install_json" ]; then
        local install_type
        install_type=$(python3 -c "import json,sys; d=json.load(open('$install_json')); print(d.get('type',''))" 2>/dev/null)
        if [ "$install_type" = "link" ]; then
            log "  Antigravity extension 为 link 模式，GEMINI.md 实时生效"
        fi
    fi

    # 5. 确保 extension-enablement.json 包含 universal-skills
    if [ -f "$enablement_file" ]; then
        if ! python3 -c "import json,sys; d=json.load(open('$enablement_file')); sys.exit(0 if 'universal-skills' in d else 1)" 2>/dev/null; then
            warn "Antigravity: universal-skills 未在 extension-enablement.json 中启用"
            warn "  请在 Antigravity 中手动启用该 extension"
        fi
    fi

    # 6. 统计技能数量
    local skill_count
    skill_count=$(find "$UNIVERSAL_SKILLS/categories" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')

    success "Antigravity extension 已就绪 ($skill_count 个技能，通过 GEMINI.md 注入)"
    log "  GEMINI.md: $extension_src/GEMINI.md"
}

# 同步到 Antigravity IDE 全局技能 (~/.gemini/config/skills/)
# Antigravity IDE 从 ~/.gemini/config/skills/<skill>/SKILL.md 加载全局技能（官方文档），
# 与 Gemini extension (~/.gemini/extensions/) 是两套机制。这里采用 per-skill 扁平 symlink
# （零磁盘开销），并跳过 project-only 技能，避免如 xiyu-server-deploy 泄漏到非 xiyu 工作区。
sync_antigravity_skills() {
    local target_root="$HOME/.gemini/config/skills"
    local skill_count=0

    mkdir -p "$target_root" || return 1

    # 清理旧的 universal-skills symlink（指向本仓库 categories/ 的）
    for entry in "$target_root"/*; do
        [ -e "$entry" ] || [ -L "$entry" ] || continue
        if [ -L "$entry" ]; then
            local dest
            dest=$(readlink "$entry")
            if [[ "$dest" == "$UNIVERSAL_SKILLS/categories/"* ]]; then
                rm -f "$entry"
            fi
        fi
    done

    # per-skill 扁平 symlink：~/.gemini/config/skills/<skill> -> categories/<cat>/<skill>
    for skill_dir in "$UNIVERSAL_SKILLS/categories"/*/*; do
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name
            skill_name="$(basename "$skill_dir")"
            # project-only 技能不进入全局，避免泄漏到非 xiyu 工作区
            if is_project_only_skill "$skill_name"; then
                continue
            fi
            local target="$target_root/$skill_name"
            if [ -e "$target" ] && [ ! -L "$target" ]; then
                # 用户同名自定义全局技能 — 优先用户版本
                continue
            fi
            # -h：同 sync_codex，裸 -sf 遇到目录 symlink 会解引用建嵌套链接
            ln -sfh "$skill_dir" "$target"
            skill_count=$((skill_count + 1))
        fi
    done

    success "Antigravity IDE 全局技能已就绪 (~/.gemini/config/skills/, $skill_count 个 symlink)"
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
        if is_syncable_skill_dir "$skill_dir"; then
            local skill_name="$(basename "$skill_dir")"
            # 全局同步：跳过项目专用技能
            if is_project_only_skill "$skill_name"; then
                continue
            fi
            ln -sfh "$skill_dir" "$plugin_dir/$version/skills/$skill_name"
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
SKIP_ZCODE=false
SKIP_TRAE_CN=false
SKIP_KIMI=false
SKIP_GROK=false
SKIP_QODER=false
SKIP_CURSOR=false
SKIP_OPENCODE=false
SKIP_PI=false
DO_DISCOVER=false
DO_PULL=false
DO_DRY_RUN=false
DO_VERIFY=false
SPECIFIC_PROJECT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-global) SKIP_GLOBAL=true ;;
        --no-projects) SKIP_PROJECTS=true ;;
        --no-codex) SKIP_CODEX=true ;;
        --no-gemini) SKIP_GEMINI=true ;;
        --no-zcode) SKIP_ZCODE=true ;;
        --no-trae-cn) SKIP_TRAE_CN=true ;;
        --no-kimi) SKIP_KIMI=true ;;
        --no-grok) SKIP_GROK=true ;;
        --no-qoder) SKIP_QODER=true ;;
        --no-cursor) SKIP_CURSOR=true ;;
        --no-opencode) SKIP_OPENCODE=true ;;
        --no-pi) SKIP_PI=true ;;
        --project=*) SPECIFIC_PROJECT="$2"; shift ;;
        --discover) DO_DISCOVER=true ;;
        --pull) DO_PULL=true ;;
        --dry-run) DO_DRY_RUN=true ;;
        --verify) DO_VERIFY=true ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --no-global     跳过全局 Claude 同步"
            echo "  --no-projects   跳过项目级同步"
            echo "  --no-codex      跳过 Codex 同步"
            echo "  --no-gemini     跳过 Gemini 同步"
            echo "  --no-zcode      跳过 ZCode 同步"
            echo "  --no-trae-cn    跳过 Trae CN Agent 同步"
            echo "  --no-kimi       跳过 Kimi Code 同步"
            echo "  --no-grok       跳过 Grok Build 同步"
            echo "  --no-cursor     跳过 Cursor skills 同步"
            echo "  --no-opencode   跳过 OpenCode 同步"
            echo "  --no-pi         跳过 PI Agent 同步"
            echo "  --project NAME  只同步指定项目"
            echo "  --discover      发现并索引项目中隐藏的技能"
            echo "  --pull          反向回流：扫描项目副本与仓库的差异，逐个确认后回流"
            echo "                 确认选项: y=整份覆盖  m=行级合并(diff3,含防丢行校验)  a=全部整份覆盖  N/q=跳过"
            echo "  --pull --dry-run  只展示差异，不回流"
            echo "  --verify        增量校验重试：只同步项目级 universal-skills 副本"
            echo "                 （diff 校验，仅重拷漂移/缺失技能；sync.sh 中断后快速自愈）"
            echo "  --help          显示此帮助"
            exit 0
            ;;
        *) shift ;;
    esac
    shift
done

log "开始同步 Universal Skills..."
echo ""

if [ "$DO_DISCOVER" = true ]; then
    discover_projects

    info "扫描项目中的隐藏技能..."
    for project_dir in "${unique_projects[@]}"; do
        project_name="$(basename "$project_dir")"
        skills_dir="$project_dir/.claude/skills"
        import_orphans "$skills_dir" "$project_name" "--scan-subdirs"
    done

    # 也扫描已知工作目录
    for base_dir in "$HOME/xiyu" "$HOME/code" "$HOME/work"; do
        if [ -d "$base_dir" ]; then
            while IFS= read -r -d '' project_skills; do
                if [ -d "$project_skills" ]; then
                    pname=$(basename "$(dirname "$(dirname "$project_skills")")")
                    import_orphans "$project_skills" "$pname" "--scan-subdirs"
                fi
            done < <(find "$base_dir" -maxdepth 3 -type d -name "skills" -path "*/.claude/skills" -print0 2>/dev/null)
        fi
    done

    success "技能发现完成！"
    echo "检查 categories/imported/ 中是否有新发现的技能。"
    exit 0
fi

if [ "$DO_PULL" = true ]; then
    log "扫描项目副本与仓库的差异..."
    echo ""
    if [ "$DO_DRY_RUN" = true ]; then
        pull_from_projects --dry-run
    else
        pull_from_projects
    fi
    exit 0
fi

if [ "$DO_VERIFY" = true ]; then
    log "增量校验重试：校验项目级 universal-skills 副本（diff 校验，漂移/缺失自愈）..."
    echo ""
    sync_projects
    exit 0
fi

if [ "$SKIP_GLOBAL" = false ]; then
    sync_claude_global
    sync_plugin
    echo ""
fi

if [ "$SKIP_PROJECTS" = false ]; then
    sync_claude_projects
    # Cursor 通过 .cursor/skills/ symlink 同步（现代 SKILL.md 机制），
    # 替代旧的 .mdc rule 生成（已废弃）。
    sync_cursor
    sync_projects
    echo ""
fi

if [ "$SKIP_CODEX" = false ]; then
    sync_codex
    echo ""
fi

if [ "$SKIP_GEMINI" = false ]; then
    sync_gemini
    sync_antigravity || true
    sync_antigravity_skills || true
    echo ""
fi

if [ "$SKIP_ZCODE" = false ]; then
    sync_zcode
    echo ""
fi

if [ "$SKIP_TRAE_CN" = false ]; then
    sync_trae_cn
    echo ""
fi

if [ "$SKIP_GROK" = false ]; then
    sync_grok
    echo ""
fi

if [ "$SKIP_KIMI" = false ]; then
    sync_kimi_code
    echo ""
fi

if [ "$SKIP_QODER" = false ]; then
    sync_qoder
    echo ""
fi

if [ "$SKIP_OPENCODE" = false ]; then
    sync_opencode
    echo ""
fi

if [ "$SKIP_PI" = false ]; then
    sync_pi
    echo ""
fi

sync_workflow_hooks
echo ""

update_skills_index

success "同步完成！"
echo ""
echo "提示："
echo "  - 本地自定义技能: $UNIVERSAL_SKILLS/local/"
echo "  - 备份位置: $BACKUP_DIR (自动保留最新 2 份)"
echo "  - 项目级技能使用实体文件（可安全提交到 git）"
echo "  - 发现项目中隐藏的技能: $0 --discover"
[ "$SKIP_GLOBAL" = false ] && echo "  - ⚠️  重启 Claude Code 以加载新 skills / 插件"
echo ""
echo "已同步的目标："
[ "$SKIP_GLOBAL" = false ] && echo "  ✓ Claude Code 插件 (~/.claude/plugins/cache/local/universal-skills/)"
[ "$SKIP_GLOBAL" = false ] && echo "  ✓ Claude Code 全局 (~/.claude/skills/) ← symlink 参考"
[ "$SKIP_PROJECTS" = false ] && echo "  ✓ Claude Code 项目级 (.claude/skills/) ← 主要"
[ "$SKIP_PROJECTS" = false ] && echo "  ✓ Cursor (~/.cursor/skills + 项目级 .cursor/skills)"
[ "$SKIP_CODEX" = false ] && echo "  ✓ Codex (~/.codex/skills/)"
[ "$SKIP_GEMINI" = false ] && echo "  ✓ Gemini CLI (extension)"
[ "$SKIP_GEMINI" = false ] && echo "  ✓ Antigravity (GEMINI.md 注入到 ~/.gemini/extensions/universal-skills/)"
[ "$SKIP_ZCODE" = false ] && echo "  ✓ ZCode (~/.agents/skills/) ← 增量 symlink; legacy ~/.zcode/skills/ 去重"
[ "$SKIP_TRAE_CN" = false ] && echo "  ✓ TraeCode (~/.trae-cn/skills/) ← 真实副本（TraeCode 不支持 symlink）"
[ "$SKIP_TRAE_CN" = false ] && echo "  ✓ TraeWork (~/.trae/skills/) ← 增量 symlink"
[ "$SKIP_GROK" = false ] && echo "  ✓ Grok Build (~/.grok/skills/) ← 增量 symlink"
[ "$SKIP_KIMI" = false ] && echo "  ✓ Kimi Code (~/.kimi-code/skills/ + config.toml)"
[ "$SKIP_QODER" = false ] && echo "  ✓ Qoder (~/.qoder/skills/) ← 增量 symlink; ~/.agents/skills/ 共享入口去重"
[ "$SKIP_OPENCODE" = false ] && echo "  ✓ OpenCode (~/.config/opencode/skills/) ← 增量 symlink"
[ "$SKIP_PI" = false ] && echo "  ✓ PI Agent (~/.pi/agent/skills/) ← 增量 symlink; ~/.agents/skills/ 共享入口去重"
[ "$SKIP_PROJECTS" = false ] && echo "  ✓ 项目级 symlinks (clawd, xiyu, etc.)"
echo "  ✓ 统一开发流程物理门禁 (PreToolUse, Stop check-review, Git pre-push)"
echo ""
