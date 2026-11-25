#!/bin/bash
set -e

cd "$(dirname "$0")"

# pydantic-core 2.33.2 supports Python through 3.13.
if command -v python3.13 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.13)"
elif command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.12)"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.11)"
else
  echo "Python 3.11, 3.12, or 3.13 is required."
  echo "Python 3.14 is not compatible with the currently pinned pydantic-core."
  exit 1
fi

command -v node >/dev/null 2>&1 || {
  echo "Node.js 18+ is required. Install it from https://nodejs.org"
  exit 1
}

echo "Using $("$PYTHON_BIN" --version)"

# Rebuild only this project's virtual environment if it is missing or uses
# an incompatible Python version. The SQLite database is not touched.
if [ -x .venv/bin/python ]; then
  VENV_VERSION="$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
else
  VENV_VERSION=""
fi

SELECTED_VERSION="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}')"

if [ "$VENV_VERSION" != "$SELECTED_VERSION" ]; then
  echo "Creating project virtual environment with Python $SELECTED_VERSION..."
  rm -rf .venv
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

echo "Installing frontend dependencies..."
(cd frontend && npm install)

echo "Starting billing software..."
(cd backend && ../.venv/bin/uvicorn app:app --reload --host 127.0.0.1 --port 8000) &
BACK_PID=$!

(cd frontend && npm run dev -- --host 127.0.0.1) &
FRONT_PID=$!

cleanup() {
  kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 3
open http://localhost:5173 2>/dev/null || true

wait
