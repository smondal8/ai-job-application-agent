#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -d .venv ]; then
    source .venv/bin/activate
elif [ -d backend/.venv ]; then
    source backend/.venv/bin/activate
fi

# Load variables from .env if present
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

echo "Starting AI Job Application Agent FastAPI Backend on http://${HOST}:${PORT}..."
echo "Swagger Docs: http://${HOST}:${PORT}/docs"
echo "Health Check: http://${HOST}:${PORT}/health"

cd "$ROOT_DIR/backend"
exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
