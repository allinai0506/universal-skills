#!/bin/bash
# Gets auth tokens for all roles and saves to /tmp/blueprint-tokens.json
#
# Usage: ./scripts/get-tokens.sh [--force] [--verbose]
#
# Output:
#   /tmp/blueprint-tokens.json
#   Also logs to /tmp/blueprint-tokens.log on --verbose
#
# Integration:
#   - Reads BACKEND_PORT from scripts/dev-env.sh
#   - Appends to memory log after successful token fetch
#   - Fails fast if backend is not responding

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"

FORCE=false
VERBOSE=false
BACKEND_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)    FORCE=true ;;
    --verbose)   VERBOSE=true ;;
    --url)       BACKEND_URL="$2"; shift ;;
    -h|--help)  echo "Usage: $0 [--force] [--verbose] [--url <url>]"; exit 0 ;;
    *)           shift ;;
  esac
  shift
done

# ---------------------------------------------------------------------------
# Detect backend URL
# ---------------------------------------------------------------------------
if [ -z "$BACKEND_URL" ]; then
  # Try dev-env.sh first
  if [ -f "$PROJECT_ROOT/scripts/dev-env.sh" ]; then
    source "$PROJECT_ROOT/scripts/dev-env.sh" 2>/dev/null || true
  fi

  # Try config.json
  local_cfg="$PROJECT_ROOT/.blueprint-config.json"
  if [ -f "$local_cfg" ]; then
    cfg_port=$(python3 -c "import json; print(json.load(open('$local_cfg'))['dev']['backend_port'])" 2>/dev/null || echo "")
    if [ -n "$cfg_port" ]; then
      export BACKEND_PORT="$cfg_port"
    fi
  fi

  BACKEND_URL="http://127.0.0.1:${BACKEND_PORT:-18081}"
fi

OUTPUT_FILE="${BLUEPRINT_TOKEN_FILE:-/tmp/blueprint-tokens.json}"
LOG_FILE="/tmp/blueprint-tokens.log"
ROLES=("bid_admin" "bid_lead" "sales" "bid_specialist")
PASSWORD="${BLUEPRINT_PASSWORD:-Test@123}"

log() {
  local msg="[$(date '+%H:%M:%S')] $1"
  echo "$msg"
  if [ "$VERBOSE" = true ]; then
    echo "$msg" >> "$LOG_FILE"
  fi
}

# ---------------------------------------------------------------------------
# Pre-flight: check backend is reachable
# ---------------------------------------------------------------------------
check_backend() {
  log "Checking backend at $BACKEND_URL..."

  if ! curl -sf --max-time 5 "$BACKEND_URL/actuator/health" > /dev/null 2>&1; then
    log "❌ Backend not reachable at $BACKEND_URL"
    log "   Make sure backend is running: mvn spring-boot:run"
    log "   Or set BACKEND_PORT=xxx before running"
    exit 1
  fi

  # Verify auth endpoint exists
  if ! curl -sf --max-time 5 -X POST "$BACKEND_URL/api/auth/login" \
       -H "Content-Type: application/json" \
       -d '{"username":"healthcheck","password":"x"}' > /dev/null 2>&1; then
    log "⚠️  Backend reachable but /api/auth/login returned non-2xx"
    log "   Auth endpoint may not be configured. Continuing anyway..."
  fi

  log "✅ Backend is responding"
}

# ---------------------------------------------------------------------------
# Fetch token for a single role
# ---------------------------------------------------------------------------
fetch_token() {
  local role="$1"
  local resp_file
  resp_file=$(mktemp)

  local resp_code
  resp_code=$(curl -sf --max-time 10 \
    -X POST "$BACKEND_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$role\",\"password\":\"$PASSWORD\"}" \
    -w "%{http_code}" \
    -o "$resp_file" 2>/dev/null || echo "000")

  local token=""
  if [ "$resp_code" = "200" ]; then
    token=$(python3 -c "
import sys, json
try:
    d = json.load(open('$resp_file'))
    t = d.get('data', {}).get('token', '')
    if t:
        print(t)
    else:
        # Try nested structure
        for v in d.values():
            if isinstance(v, dict) and 'token' in v:
                print(v['token'])
                sys.exit(0)
        print('')
except: print('')
" 2>/dev/null || echo "")

    if [ -n "$token" ]; then
      log "  ✅ $role: token obtained (${#token} chars)"
    else
      log "  ❌ $role: HTTP 200 but no token in response"
      if [ "$VERBOSE" = true ]; then
        log "     Response: $(cat "$resp_file")"
      fi
    fi
  else
    log "  ❌ $role: HTTP $resp_code"
    if [ "$VERBOSE" = true ]; then
      log "     Response: $(cat "$resp_file")"
    fi
  fi

  rm -f "$resp_file"
  echo "$token"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
log "=== Blueprint Token Fetcher ==="
log "Backend: $BACKEND_URL"
log "Output:  $OUTPUT_FILE"
log ""

check_backend

declare -A TOKEN_MAP
failed=0

for role in "${ROLES[@]}"; do
  token=$(fetch_token "$role")
  if [ -n "$token" ]; then
    TOKEN_MAP[$role]="$token"
  else
    failed=$((failed + 1))
  fi
done

# Write output JSON
log ""
log "Writing tokens to $OUTPUT_FILE..."
{
  echo "{"
  first=true
  for role in "${ROLES[@]}"; do
    if [ -n "${TOKEN_MAP[$role]:-}" ]; then
      [ "$first" = true ] && first=false || echo ","
      printf '  "%s": "%s"' "$role" "${TOKEN_MAP[$role]}"
    fi
  done
  echo ""
  echo "}"
} > "$OUTPUT_FILE"

# Summary
success=$((${#ROLES[@]} - failed))
log ""
if [ $failed -eq 0 ]; then
  log "✅ All $success tokens obtained successfully"
else
  log "⚠️  $success/${#ROLES[@]} tokens obtained ($failed failed)"
  log "   Failed roles may need seed data in the database"
fi

# Print summary table
echo ""
echo "Token summary:"
python3 -c "
import json, sys
try:
    d = json.load(open('$OUTPUT_FILE'))
    for k, v in d.items():
        status = '✅' if v else '❌'
        print(f'  {status} {k}')
except Exception as e:
    print(f'  ❌ Could not parse output: {e}')
"

# Append to memory log if CLAUDE_PLUGIN_DATA is set
if [ -n "${CLAUDE_PLUGIN_DATA:-}" ] && [ $failed -eq 0 ]; then
  memory_log="$CLAUDE_PLUGIN_DATA/token-fetch-log.jsonl"
  mkdir -p "$(dirname "$memory_log")"
  echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"backend\":\"$BACKEND_URL\",\"roles\":${#ROLES[@]},\"success\":$success}" >> "$memory_log" 2>/dev/null || true
fi

exit $failed
