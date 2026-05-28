#!/usr/bin/env sh
set -eu

export PORT="${PORT:-8080}"

uv run python main.py &
BACKEND_PID="$!"

cleanup() {
  kill "$BACKEND_PID" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

nginx -g "daemon off;"

