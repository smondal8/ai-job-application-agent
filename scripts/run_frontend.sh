#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/frontend"

echo "Starting AI Job Application Agent Frontend (Vite) on http://127.0.0.1:5173..."
exec npm run dev -- --host 127.0.0.1 --port 5173
