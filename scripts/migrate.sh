#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -d .venv ]; then
    source .venv/bin/activate
elif [ -d backend/.venv ]; then
    source backend/.venv/bin/activate
fi

cd "$ROOT_DIR/backend"
echo "Applying database migrations with Alembic..."
alembic upgrade head
echo "Migrations applied successfully."
