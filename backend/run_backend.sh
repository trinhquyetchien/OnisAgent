#!/usr/bin/env bash
set -e

PORT=${1:-8000}
HOST=${HOST:-"0.0.0.0"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================================="
echo "    Khởi chạy OnisAgent FastAPI Backend tại http://${HOST}:${PORT}"
echo "=========================================================="

cd "$SCRIPT_DIR"

# Reuse root .venv if present or create local one
if [ -f "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
else
    echo "[1/2] Đang khởi tạo virtualenv cho backend..."
    uv venv "$SCRIPT_DIR/.venv" --python /usr/bin/python3.12 || python3 -m venv "$SCRIPT_DIR/.venv"
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
fi

echo "[2/2] Chạy máy chủ FastAPI Uvicorn..."
exec "$PYTHON_BIN" -m uvicorn app.main:app --app-dir "$SCRIPT_DIR" --host "$HOST" --port "$PORT" --reload
