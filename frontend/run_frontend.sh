#!/usr/bin/env bash
set -e

PORT=${1:-3000}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "    Khởi chạy OnisAgent Web Frontend tại http://localhost:${PORT}"
echo "    (Đang kết nối tới Backend API tại http://localhost:8000)"
echo "=========================================================="

cd "$SCRIPT_DIR"

if command -v python3 >/dev/null 2>&1; then
    exec python3 -m http.server "$PORT"
elif command -v npx >/dev/null 2>&1; then
    exec npx serve -l "$PORT" .
else
    echo "Lỗi: Không tìm thấy Python3 hoặc Node.js để chạy web server!"
    exit 1
fi
