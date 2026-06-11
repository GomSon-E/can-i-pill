#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

COMPOSE=(docker compose)

if ! docker compose version >/dev/null 2>&1; then
  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose)
  else
    echo "Docker Compose is not installed."
    exit 1
  fi
fi

ENV_FILE="${ENV_FILE:-.env.dev}"
if [ ! -f "$ENV_FILE" ] && [ -f .env ]; then
  ENV_FILE=".env"
fi

if [ ! -f "$ENV_FILE" ]; then
  cat <<'MSG'
.env.dev file is missing.

Create .env.dev in the project root with at least:
  GEMINI_API_KEY=...

You can also keep using .env; this script falls back to .env when .env.dev is absent.
For local Docker Compose, AI_SERVER_URL is set automatically to http://ai_server:8001.
MSG
  exit 1
fi

export APP_ENV_FILE="$ENV_FILE"
export BACKEND_HOST="${BACKEND_HOST:-backend}"
export FRONTEND_PORT="${FRONTEND_PORT:-8080}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export AI_SERVER_PORT="${AI_SERVER_PORT:-8001}"

case "${1:-up}" in
  up)
    "${COMPOSE[@]}" up --build
    ;;
  up-d)
    "${COMPOSE[@]}" up --build -d
    cat <<MSG

Docker dev stack is running:
  Env file: $APP_ENV_FILE
  Frontend: http://localhost:$FRONTEND_PORT
  Backend:  http://localhost:$BACKEND_PORT
  AI:       http://localhost:$AI_SERVER_PORT

Use ./run-docker-dev.sh logs to follow logs.
MSG
    ;;
  down)
    "${COMPOSE[@]}" down
    ;;
  restart)
    "${COMPOSE[@]}" down
    "${COMPOSE[@]}" up --build
    ;;
  logs)
    "${COMPOSE[@]}" logs -f "${@:2}"
    ;;
  ps)
    "${COMPOSE[@]}" ps
    ;;
  *)
    cat <<'MSG'
Usage:
  ./run-docker-dev.sh        # build and run all services
  ./run-docker-dev.sh up-d   # build and run in background
  ./run-docker-dev.sh down   # stop services
  ./run-docker-dev.sh logs   # follow logs
  ./run-docker-dev.sh ps     # show service status

Optional:
  ENV_FILE=.env.local FRONTEND_PORT=5174 ./run-docker-dev.sh up-d
MSG
    exit 1
    ;;
esac
