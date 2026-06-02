#!/usr/bin/env sh
set -eu

API_URL="${SENTINELX_API_URL:-http://localhost:8000}"
API_KEY="${SENTINELX_API_KEY:-}"
AUTH_LOG="${SENTINELX_AUTH_LOG:-/var/log/auth.log}"
LIMIT="${SENTINELX_COLLECTOR_LIMIT:-200}"

if [ ! -r "$AUTH_LOG" ]; then
  echo "Cannot read $AUTH_LOG"
  exit 1
fi

tail -n "$LIMIT" "$AUTH_LOG" | while IFS= read -r line; do
  payload=$(printf '%s' "$line" | python3 -c 'import json,sys; print(json.dumps({"message": sys.stdin.read(), "host": "linux-host"}))')
  curl -fsS -X POST "$API_URL/api/logs/collectors/linux" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "{\"event\":$payload}" >/dev/null
done
