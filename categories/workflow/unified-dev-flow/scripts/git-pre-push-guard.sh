#!/usr/bin/env bash
# Git pre-push hook for unified-dev-flow S6 Code Review enforcement.
# Intercepts 'git push' to ensure task branches have completed S6 Code Review (MERGE_READY).
set -euo pipefail

CHECKER="${HOME}/.claude/scripts/entry-gate-check.py"
if [[ ! -f "$CHECKER" ]]; then
  # Fallback to repo-relative path if available
  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  CHECKER="${REPO_ROOT}/categories/workflow/unified-dev-flow/scripts/entry-gate-check.py"
fi

if [[ -f "$CHECKER" ]]; then
  exec python3 "$CHECKER" --guard-push "$@"
fi

# If checker is completely unavailable, fail open with warning (do not deadlock git)
echo "⚠️ [unified-dev-flow] 找不到 entry-gate-check.py，pre-push 审查门禁降级放行。" >&2
exit 0
