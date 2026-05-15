#!/usr/bin/env bash
# Generic typeset-engine renderer.
# Posts JSON, saves binary response, validates HTTP 200.
# Usage: render.sh <endpoint> <json_file> <output_file> [query_string]
set -e

ENDPOINT="${1:-}"
JSON_FILE="${2:-}"
OUT_FILE="${3:-}"
QS="${4:-}"
BASE="${TYPESET_BASE:-http://localhost:9091}"

if [ -z "$ENDPOINT" ] || [ -z "$JSON_FILE" ] || [ -z "$OUT_FILE" ]; then
    echo "Usage: $0 <endpoint> <json_file> <output_file> [query_string]" >&2
    echo "  e.g.  $0 /render/pdf payload.json out.pdf 'theme=cicc'" >&2
    exit 2
fi

[ -f "$JSON_FILE" ] || { echo "ERROR: $JSON_FILE not found" >&2; exit 2; }

URL="${BASE}${ENDPOINT}"
[ -n "$QS" ] && URL="${URL}?${QS}"

mkdir -p "$(dirname "$OUT_FILE")"

HTTP=$(curl -sS -o "$OUT_FILE" -w "%{http_code}" \
    -X POST "$URL" \
    -H 'Content-Type: application/json' \
    --data-binary "@$JSON_FILE")

if [ "$HTTP" != "200" ]; then
    echo "ERROR: HTTP $HTTP from $URL" >&2
    echo "--- response body (first 1000 bytes) ---" >&2
    head -c 1000 "$OUT_FILE" >&2 || true
    echo >&2
    rm -f "$OUT_FILE"
    exit 1
fi

SIZE=$(stat -c %s "$OUT_FILE")
echo "OK: HTTP 200, $OUT_FILE ($SIZE bytes)"
