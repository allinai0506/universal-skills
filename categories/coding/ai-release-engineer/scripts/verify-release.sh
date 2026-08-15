#!/usr/bin/env bash
set -euo pipefail

echo "== AI Release Engineer: local verification =="

if [ -f package.json ]; then
  echo "[INFO] Node project detected"
  if command -v npm >/dev/null 2>&1; then
    npm run build --if-present
    npm test --if-present
  else
    echo "[ERROR] npm not found"
    exit 1
  fi
elif [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  echo "[INFO] Python project detected"
  if command -v python >/dev/null 2>&1; then
    python -m compileall .
    if command -v pytest >/dev/null 2>&1; then
      pytest
    else
      echo "[WARN] pytest not found; run the repository's canonical test command in CI"
    fi
  else
    echo "[ERROR] python not found"
    exit 1
  fi
else
  echo "[WARN] Project type not detected."
  echo "[WARN] Use the repository's canonical build/test commands."
fi

echo "== Local verification completed =="
