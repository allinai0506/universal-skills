#!/bin/bash

# Read-only audit for skill roots that are visible to the same runtime.
# The Codex root may contain .system, but it must not contain a universal-skills
# symlink when ~/.agents/skills already provides the same skill name.

set -euo pipefail

SOURCE_ROOT="${UNIVERSAL_SKILLS_ROOT:-$(cd "$(dirname "$0")/.." && pwd -P)}"
CODEX_ROOT="${CODEX_SKILLS_ROOT:-$HOME/.codex/skills}"
AGENTS_ROOT="${AGENTS_SKILLS_ROOT:-$HOME/.agents/skills}"
errors=0
codex_skills=0
agents_skills=0
duplicates=0

count_skills() {
    local root="$1"
    [ -d "$root" ] || { echo 0; return 0; }
    find -L "$root" -mindepth 2 -maxdepth 2 -type f -name SKILL.md -print 2>/dev/null | wc -l | tr -d ' '
}

codex_skills="$(count_skills "$CODEX_ROOT")"
agents_skills="$(count_skills "$AGENTS_ROOT")"

if [ ! -d "$CODEX_ROOT" ]; then
    echo "SKILL_ROOTS_SKIP codex_root_missing=$CODEX_ROOT"
    exit 0
fi

for entry in "$CODEX_ROOT"/*; do
    [ -e "$entry" ] || [ -L "$entry" ] || continue
    [ -L "$entry" ] || continue

    name="$(basename "$entry")"
    target="$(readlink "$entry" 2>/dev/null || true)"

    case "$target" in
        "$SOURCE_ROOT/categories/"*)
            if [ ! -f "$entry/SKILL.md" ]; then
                echo "ERROR broken_universal_link name=$name target=$target" >&2
                errors=$((errors + 1))
            fi
            ;;
        *)
            continue
            ;;
    esac

    if [ -f "$AGENTS_ROOT/$name/SKILL.md" ]; then
        echo "ERROR cross_root_duplicate name=$name codex=$entry agents=$AGENTS_ROOT/$name" >&2
        duplicates=$((duplicates + 1))
        errors=$((errors + 1))
    fi
done

if [ "$duplicates" -eq 0 ] && [ "$errors" -eq 0 ]; then
    echo "SKILL_ROOTS_OK codex_skills=$codex_skills agents_skills=$agents_skills source=$SOURCE_ROOT"
    exit 0
fi

echo "SKILL_ROOTS_FAIL codex_skills=$codex_skills agents_skills=$agents_skills duplicates=$duplicates errors=$errors" >&2
exit 1
