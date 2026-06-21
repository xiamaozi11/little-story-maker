#!/usr/bin/env bash
# 启动 StoryCraft API 后端（供 Android 移动端使用）
set -e
cd "$(dirname "$0")/../src"
python -m uvicorn api_server:app --host 0.0.0.0 --port "${API_PORT:-8000}" --reload
