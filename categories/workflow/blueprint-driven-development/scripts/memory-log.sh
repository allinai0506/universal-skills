#!/bin/bash
# Append-only gap-analysis memory log for blueprint-driven-development
#
# 每完成一次 Phase 2 差距分析，将结果追加到 .blueprint-data/gap-analysis-log.jsonl
# 下次运行时读取历史，可以告诉 Agent："上次分析 §4.2.1 的结论是..."
#
# 用法：
#   bash scripts/memory-log.sh append <section> <gap_md_path> [notes]
#   bash scripts/memory-log.sh read [--section <section>] [--recent N]
#   bash scripts/memory-log.sh diff <section-a> <section-b>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="${CLAUDE_PLUGIN_DATA:-$SKILL_DIR/.blueprint-data}"
LOG_FILE="$DATA_DIR/gap-analysis-log.jsonl"

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
init() {
  if [ ! -d "$DATA_DIR" ]; then
    mkdir -p "$DATA_DIR"
  fi
  if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
  fi
}

# ---------------------------------------------------------------------------
# Append a new gap-analysis record
# ---------------------------------------------------------------------------
append() {
  local section="$1"
  local gap_md_path="$2"
  local notes="${3:-}"

  init

  local worktree
  worktree=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")

  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  local impl_count="0"
  local gap_count="0"
  local partial_count="0"

  # Parse counts from gap-analysis.md if it exists
  if [ -f "$gap_md_path" ]; then
    impl_count=$(grep -c "✅ 已实现\|已完整实现" "$gap_md_path" 2>/dev/null || echo "0")
    gap_count=$(grep -c "❌ 未实现" "$gap_md_path" 2>/dev/null || echo "0")
    partial_count=$(grep -c "⚠️ 部分实现" "$gap_md_path" 2>/dev/null || echo "0")
  fi

  local entry
  entry=$(printf '%s' "{\"timestamp\":\"$timestamp\",\"section\":\"$section\",\"worktree\":\"$worktree\",\"gap_file\":\"$gap_md_path\",\"implemented\":$impl_count,\"gaps\":$gap_count,\"partial\":$partial_count,\"notes\":\"$notes\"}")

  echo "$entry" >> "$LOG_FILE"

  echo "✅ Logged: $section (impl=$impl_count, gaps=$gap_count, partial=$partial_count)"
}

# ---------------------------------------------------------------------------
# Read / query records
# ---------------------------------------------------------------------------
read_logs() {
  init

  local section_filter=""
  local recent_n=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --section) section_filter="$2"; shift 2 ;;
      --recent)  recent_n="$2"; shift 2 ;;
      *)         shift ;;
    esac
  done

  if [ ! -s "$LOG_FILE" ]; then
    echo "📭 No gap-analysis history yet."
    return
  fi

  local count=0
  local total_impl=0
  local total_gaps=0

  echo "=== Gap-Analysis History ==="
  echo ""

  while IFS= read -r line; do
    local sec impl gaps partial ts
    sec=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('section',''))" 2>/dev/null || echo "?")
    impl=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('implemented',0))" 2>/dev/null || echo "?")
    gaps=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('gaps',0))" 2>/dev/null || echo "?")
    partial=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('partial',0))" 2>/dev/null || echo "?")
    ts=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('timestamp','')[:10])" 2>/dev/null || echo "?")

    if [ -n "$section_filter" ] && [ "$sec" != "$section_filter" ]; then
      continue
    fi

    printf "  %-12s  impl=%-3s  gaps=%-3s  partial=%-2s  (%s)\n" "$sec" "$impl" "$gaps" "$partial" "$ts"
    count=$((count + 1))
    total_impl=$((total_impl + impl))
    total_gaps=$((total_gaps + gaps))
  done < "$LOG_FILE"

  echo ""
  echo "Total: $count sections | implemented: $total_impl | gaps: $total_gaps"
}

# ---------------------------------------------------------------------------
# Diff two sections
# ---------------------------------------------------------------------------
diff_sections() {
  init

  local a="$1"
  local b="$2"

  local line_a line_b
  line_a=$(grep "\"section\":\"$a\"" "$LOG_FILE" | tail -1 || echo "")
  line_b=$(grep "\"section\":\"$b\"" "$LOG_FILE" | tail -1 || echo "")

  if [ -z "$line_a" ]; then
    echo "⚠️  No record for section: $a"
  fi
  if [ -z "$line_b" ]; then
    echo "⚠️  No record for section: $b"
  fi

  echo "Section A: $a"
  echo "$line_a" | python3 -m json.tool 2>/dev/null || echo "$line_a"
  echo ""
  echo "Section B: $b"
  echo "$line_b" | python3 -m json.tool 2>/dev/null || echo "$line_b"
}

# ---------------------------------------------------------------------------
# CLI routing
# ---------------------------------------------------------------------------
init

case "${1:-}" in
  append) append "${2:-}" "${3:-}" "${4:-}" ;;
  read)   read_logs "${@:2}" ;;
  diff)   diff_sections "${2:-}" "${3:-}" ;;
  *)      echo "Usage: $0 {append|read|diff} [args...]"
          echo "  append <section> <gap_md_path> [notes]"
          echo "  read [--section <section>] [--recent N]"
          echo "  diff <section-a> <section-b>" ;;
esac
