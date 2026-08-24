#!/usr/bin/env bash
set -euo pipefail

echo "================================================================="
echo "  AI Job Application Agent - Phase 9 End-to-End Smoke Test"
echo "  Playwright Browser Application-Preparation Engine & Safety Guard"
echo "================================================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo "Step 1: Activating Virtual Environment..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "backend/.venv" ]; then
    source backend/.venv/bin/activate
else
    echo "Error: Virtual environment not found."
    exit 1
fi

echo ""
echo "Step 2: Checking Playwright Installation..."
python -c "import importlib.metadata; print(f'Playwright Version: {importlib.metadata.version(\"playwright\")}')"

echo ""
echo "Step 3: Verifying Database Migrations..."
cd backend
alembic upgrade head
cd "$ROOT_DIR"

echo ""
echo "Step 4: Executing Phase 9 Dedicated Test Suite..."
pytest backend/tests/test_preparation_safety_guards.py \
       backend/tests/test_browser_preparation_engine.py \
       backend/tests/test_phase9_api.py -v

echo ""
echo "Step 5: Executing Full Regression Test Suite (Phases 1-9)..."
pytest backend/tests -v

echo ""
echo "Step 6: Verifying React Frontend Build..."
cd frontend
npm run build
cd "$ROOT_DIR"

echo ""
echo "================================================================="
echo "  PHASE 9 VERIFICATION SUCCESSFUL!"
echo "  Playwright Browser Application-Preparation Engine Verified."
echo "  Final Submit Guard Invariant Strictly Maintained (Never Clicked)."
echo "================================================================="
