#!/usr/bin/env bash
# Ensure typeset-engine container is up and /health is OK.
# Idempotent: starts container if missing, restarts if stopped, no-op if already healthy.
# Forwards GEMINI_API_KEY from host env if present (required for AI endpoints).
set -e

PORT=9091
NAME=typeset-engine
IMAGE=typeset-engine:v3
OUT_DIR=/tmp/typeset-output

mkdir -p "$OUT_DIR"

# Already healthy?
if curl -sf "http://localhost:$PORT/health" >/dev/null 2>&1; then
    echo "OK: typeset-engine already healthy on :$PORT"
    exit 0
fi

# Probe docker accessibility (without sudo). User must be in 'docker' group.
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: docker daemon not accessible. Either:" >&2
    echo "  - re-login so 'docker' group takes effect, or" >&2
    echo "  - run 'newgrp docker' in this shell" >&2
    exit 2
fi

# Image must exist
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "ERROR: image $IMAGE not found. Build it first:" >&2
    echo "  cd <typeset-engine repo> && docker build -t $IMAGE ." >&2
    exit 3
fi

# Container exists but stopped → start; else create new
if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
    echo "Container exists but unhealthy/stopped. Restarting..."
    docker start "$NAME" >/dev/null
else
    echo "Creating new container..."
    EXTRA=""
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        EXTRA="-e GEMINI_API_KEY=$GEMINI_API_KEY"
        echo "  GEMINI_API_KEY: forwarded from host env"
    else
        echo "  GEMINI_API_KEY: not set (AI endpoints will 500)"
    fi
    docker run -d --name "$NAME" -p "$PORT:9090" \
        $EXTRA \
        -v "$OUT_DIR:/app/output" \
        "$IMAGE" >/dev/null
fi

# Wait for /health (start_period in Dockerfile = 40s)
echo -n "Waiting for /health"
for i in $(seq 1 60); do
    if curl -sf "http://localhost:$PORT/health" >/dev/null 2>&1; then
        echo " OK"
        exit 0
    fi
    echo -n "."
    sleep 1
done

echo
echo "ERROR: timeout (60s) waiting for /health" >&2
echo "--- container logs (tail 30) ---" >&2
docker logs --tail 30 "$NAME" >&2 || true
exit 1
