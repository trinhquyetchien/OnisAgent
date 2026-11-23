#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
APP_DIR="$ROOT_DIR/app"
BACKEND_ENV="$BACKEND_DIR/.env"
APP_ENV="$APP_DIR/.env"
API_BASE_URL="http://127.0.0.1:8000"

read_env_value() {
  local file="$1"
  local key="$2"
  awk -F= -v wanted="$key" '$1 == wanted {sub(/^[^=]*=/, ""); print; exit}' "$file" \
    | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
}

fail() {
  echo "[run] ERROR: $*" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || fail "Docker is required."
docker compose version >/dev/null 2>&1 || fail "Docker Compose plugin is required."
command -v flutter >/dev/null 2>&1 || fail "Flutter is required."

[ -f "$BACKEND_ENV" ] || fail "Missing backend/.env. Copy backend/.env.example and set real secrets first."

postgres_password="$(read_env_value "$BACKEND_ENV" POSTGRES_PASSWORD)"
auth_secret="$(read_env_value "$BACKEND_ENV" AUTH_SECRET)"

[ -n "$postgres_password" ] || fail "POSTGRES_PASSWORD is empty in backend/.env."
[ "$postgres_password" != "CHANGE_ME_TO_A_STRONG_PASSWORD" ] || fail "Replace the PostgreSQL password in backend/.env."
[ -n "$auth_secret" ] || fail "AUTH_SECRET is empty in backend/.env."
[ "$auth_secret" != "replace-with-a-long-random-secret" ] || fail "Replace AUTH_SECRET in backend/.env."

if [ -f "$APP_ENV" ]; then
  configured_api_url="$(read_env_value "$APP_ENV" API_BASE_URL)"
  [ -n "$configured_api_url" ] && API_BASE_URL="$configured_api_url"
fi

echo "[run] Starting PostgreSQL and FastAPI with Docker..."
(
  cd "$BACKEND_DIR"
  docker compose up -d --build
  docker compose run --rm backend alembic upgrade head
)

if command -v curl >/dev/null 2>&1 && curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "[run] Ollama is available."
else
  echo "[run] WARNING: Ollama is not available; reasoning requests will report unavailable."
  echo "[run] Start it separately with: ollama serve"
  echo "[run] Install the configured model with: ollama pull qwen2.5:3b"
fi

echo "[run] Starting Flutter Web against $API_BASE_URL"
cd "$APP_DIR"
flutter pub get
exec flutter run \
  -d chrome \
  --web-hostname localhost \
  --web-port 7357 \
  "--dart-define=API_BASE_URL=$API_BASE_URL"
