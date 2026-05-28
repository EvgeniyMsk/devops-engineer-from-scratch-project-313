#!/usr/bin/env sh
set -eu

PUBLIC_PORT="${PORT:-80}"
BACKEND_PORT="8080"

# Render expects the service to listen on $PORT.
# We'll keep backend on 8080 and expose it via Nginx on $PUBLIC_PORT.
export PUBLIC_PORT
PORT="${BACKEND_PORT}" uv run python main.py &
BACKEND_PID="$!"

envsubst '${PUBLIC_PORT}' < /app/nginx.conf.template \
  > /etc/nginx/sites-enabled/default

cleanup() {
  kill "$BACKEND_PID" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

nginx -g "daemon off;"

