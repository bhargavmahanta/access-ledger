#!/usr/bin/env bash
# Run API and Vite together; Ctrl+C terminates both.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="$ROOT/.tools/node/current/bin:$PATH"
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!
trap 'kill "$API_PID" ${UI_PID:-} 2>/dev/null || true' EXIT INT TERM
npm --prefix frontend run dev -- --port 5173 --strictPort &
UI_PID=$!
wait -n "$API_PID" "$UI_PID"
