#!/bin/bash
# Gets auth tokens for all roles and saves to /tmp/blueprint-tokens.json
# Usage: ./scripts/get-tokens.sh
# Output: /tmp/blueprint-tokens.json  ← 供验证阶段使用

set -euo pipefail

# 自动检测 dev-env
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$PROJECT_ROOT/scripts/dev-env.sh" ]; then
  source "$PROJECT_ROOT/scripts/dev-env.sh" 2>/dev/null || true
fi

BASE_URL="http://127.0.0.1:${BACKEND_PORT:-18081}"

ROLES=("bid_admin" "bid_lead" "sales" "bid_specialist")
PASSWORD="${BLUEPRINT_PASSWORD:-Test@123}"

echo "{" > /tmp/blueprint-tokens.json
FIRST=true
for ROLE in "${ROLES[@]}"; do
  RESP=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ROLE\",\"password\":\"$PASSWORD\"}" 2>/dev/null)
  TOKEN=$(echo "$RESP" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('data', {}).get('token', ''))
except: print('')" 2>/dev/null || echo "")

  if [ "$FIRST" = true ]; then FIRST=false; else echo "," >> /tmp/blueprint-tokens.json; fi
  echo "  \"$ROLE\": \"$TOKEN\"" >> /tmp/blueprint-tokens.json
done
echo "}" >> /tmp/blueprint-tokens.json

echo "✅ Tokens saved to /tmp/blueprint-tokens.json"
python3 -c "import json; d=json.load(open('/tmp/blueprint-tokens.json')); [print(f'  {k}: {\"✅\" if v else \"❌\"}') for k,v in d.items()]" 2>/dev/null
