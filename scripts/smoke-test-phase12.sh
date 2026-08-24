#!/usr/bin/env bash
set -euo pipefail

echo "================================================================="
echo "  AI Job Application Agent - Phase 12 End-to-End Smoke Test"
echo "  Complete System Stabilization, E2E Verification & Release"
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
echo "Step 2: Checking Backend Dependencies & Playwright..."
python -c "import fastapi, sqlalchemy, alembic, pydantic, playwright; print('Core Backend Dependencies: OK')"

echo ""
echo "Step 3: Verifying Database Migrations (Alembic)..."
cd backend
alembic upgrade head
cd "$ROOT_DIR"

echo ""
echo "Step 4: Executing Dedicated Phase 12 Integration & Negative Suites..."
pytest backend/tests/test_phase12_e2e_complete_pipeline.py \
       backend/tests/test_phase12_negative_security_suite.py -v

echo ""
echo "Step 5: Executing Complete Full Test Suite (130 Tests across Phases 1-12)..."
pytest backend/tests -v

echo ""
echo "Step 6: Live Local Ollama Connectivity Smoke Test (qwen3:8b)..."
python -c "
import urllib.request, json
try:
    req = urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=2)
    models = json.loads(req.read().decode('utf-8')).get('models', [])
    model_names = [m.get('name') for m in models]
    print(f'Local Ollama Status: CONNECTED. Models available: {model_names}')
except Exception as e:
    print(f'Local Ollama Notice: {e} (Suite runs with mocked LLM isolation)')
"

echo ""
echo "Step 7: Verifying React Frontend Production Build..."
cd frontend
npm run build
cd "$ROOT_DIR"

echo ""
echo "================================================================="
echo "  PHASE 12 VERIFICATION SUCCESSFUL!"
echo "  Full System Stabilization & Release Milestones Complete."
echo "  Strict Security Invariants Confirmed:"
echo "  1. End-to-End Pipeline: Discovery -> Analysis -> Tailor -> Review -> Approval -> Staging -> Submit Guard."
echo "  2. No approval means NO browser preparation (Strictly 403 Forbidden)."
echo "  3. Changed resume, JD, candidate, or answers immediately invalidates approval."
echo "  4. Unsupported challenges (CAPTCHA / Auth) pause safely without crashing."
echo "  5. Final submit button is NEVER automated or clicked."
echo "================================================================="
