#!/usr/bin/env bash
set -euo pipefail

echo "================================================================="
echo "  AI Job Application Agent - Phase 11 End-to-End Smoke Test"
echo "  Hardening, Observability, Resilience, Redaction & Disaster Recovery"
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
echo "Step 2: Checking Dependencies & Environment..."
python -c "import fastapi, sqlalchemy, alembic, pydantic, playwright; print('Core Backend Dependencies: OK')"

echo ""
echo "Step 3: Verifying Database Migrations (Alembic)..."
cd backend
alembic upgrade head
cd "$ROOT_DIR"

echo ""
echo "Step 4: Executing Dedicated Phase 11 Hardening & Security Tests..."
pytest backend/tests/test_security_boundaries_and_adversarial.py \
       backend/tests/test_idempotency_and_duplicates.py \
       backend/tests/test_redaction_service.py \
       backend/tests/test_backup_restore_service.py \
       backend/tests/test_crash_recovery_service.py \
       backend/tests/test_phase11_api.py -v

echo ""
echo "Step 5: Executing Full Complete Test Suite (Phases 1-11)..."
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
    print(f'Local Ollama Notice: {e} (Unit tests run fully with mocked LLM isolation)')
"

echo ""
echo "Step 7: Verifying React Frontend Production Build..."
cd frontend
npm run build
cd "$ROOT_DIR"

echo ""
echo "================================================================="
echo "  PHASE 11 VERIFICATION SUCCESSFUL!"
echo "  Hardening, Observability, Resilience, Redaction & Recovery Complete."
echo "  Strict Security Invariants Confirmed:"
echo "  1. Untrusted Input Policy Active (JDs, pages, employer text sanitized)."
echo "  2. LLM cannot change approvals, authorize submissions, or disable guards."
echo "  3. Human Approval Gate strictly enforced before any browser staging."
echo "  4. Final-Submit Guard Invariant strictly maintained (Never Clicked)."
echo "  5. Idempotency, Redaction, Crash Recovery, and Backups Verified."
echo "================================================================="
