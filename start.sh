#!/bin/bash
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Install Python 3.10+"; exit 1; }
command -v node >/dev/null || { echo "Install Node.js 18+ from https://nodejs.org"; exit 1; }
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
(cd frontend && npm install)
(cd backend && ../.venv/bin/uvicorn app:app --reload --host 127.0.0.1 --port 8000) &
BACK_PID=$!
(cd frontend && npm run dev -- --host 127.0.0.1) &
FRONT_PID=$!
cleanup(){ kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
sleep 3
open http://localhost:5173 2>/dev/null || true
wait
