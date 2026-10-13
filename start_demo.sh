#!/usr/bin/env bash
set -e

PORT=${1:-8000}
HOST=${HOST:-"0.0.0.0"}

echo "=========================================================="
echo "         Khởi chạy OnisAgent Web Demo (Voice + AI)        "
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure venv exists
if [ ! -d ".venv" ]; then
    echo "[1/3] Đang khởi tạo môi trường Python virtualenv..."
    uv venv .venv --python /usr/bin/python3.12
fi

# Ensure dependencies installed
echo "[2/3] Kiểm tra thư viện phụ thuộc..."
uv pip install --python .venv/bin/python fastapi uvicorn pydantic requests httpx > /dev/null 2>&1

echo "[3/3] Khởi động máy chủ OnisAgent tại http://localhost:${PORT}"
echo "----------------------------------------------------------"
echo "  • System 1 Model : Kev (jaredpalmer/kev)"
echo "  • Reasoning LLM  : Ollama (qwen2.5:3b / gemma3:latest)"
echo "  • Data Storage   : data/onis_db.json"
echo "  • Voice Interface: Web Speech API (STT & TTS)"
echo "----------------------------------------------------------"

exec .venv/bin/python -m uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
