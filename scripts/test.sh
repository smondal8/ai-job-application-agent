#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -d .venv ]; then
    source .venv/bin/activate
elif [ -d backend/.venv ]; then
    source backend/.venv/bin/activate
fi

echo "================================================================"
echo "1. Running Backend Test Suite (pytest)"
echo "================================================================"
cd "$ROOT_DIR/backend"
pytest -v

echo ""
echo "================================================================"
echo "2. Running Frontend Typecheck & Build (tsc + vite build)"
echo "================================================================"
cd "$ROOT_DIR/frontend"
npm run build

echo ""
echo "================================================================"
echo " All Tests & Builds Passed Successfully!"
echo "================================================================"
