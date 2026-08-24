#!/usr/bin/env bash
set -e

echo "================================================================"
echo "AI Job Application Agent - Environment Setup (v1.0.0)"
echo "================================================================"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# 1. Check Python version
echo "[1/6] Checking Python 3.12+ requirement..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 could not be found. Please install Python 3.12+."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Detected Python: $PYTHON_VERSION"

# 2. Check Node & NPM
echo "[2/6] Checking Node.js and NPM..."
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm could not be found. Please install Node.js."
    exit 1
fi
echo "Detected Node: $(node --version), NPM: $(npm --version)"

# 3. Setup .env file
if [ ! -f .env ]; then
    echo "[3/6] Initializing .env from .env.example..."
    cp .env.example .env
else
    echo "[3/6] Existing .env file found."
fi

# 4. Setup Python Virtual Environment and install dependencies
echo "[4/6] Setting up virtual environment (.venv) & installing backend dependencies..."
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements-dev.txt

# Install Playwright browser binaries
echo "Installing Playwright browser binaries (Chromium)..."
playwright install chromium

# 5. Setup Frontend dependencies
echo "[5/6] Installing frontend dependencies & building static bundle..."
cd "$ROOT_DIR/frontend"
npm install
npm run build

cd "$ROOT_DIR/backend"
echo "Running database migrations with Alembic..."
alembic upgrade head

# 6. Check Local Ollama Engine
echo "[6/6] Checking Local Ollama Subsystem..."
python3 -c "
import urllib.request, json
try:
    req = urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=2)
    models = json.loads(req.read().decode('utf-8')).get('models', [])
    names = [m.get('name') for m in models]
    print(f'Ollama connected. Available models: {names}')
    if not any('qwen3:8b' in n for n in names):
        print('NOTE: Run \"ollama pull qwen3:8b\" to download the recommended model.')
except Exception as e:
    print('NOTE: Ollama is not currently running. Start it via \"ollama serve\" when analyzing JDs.')
"

echo ""
echo "================================================================"
echo " Setup Completed Successfully!"
echo " - To run backend:    ./scripts/run_backend.sh"
echo " - To run frontend:   ./scripts/run_frontend.sh"
echo " - To run test suite: ./scripts/test.sh"
echo " - To run smoke test: ./scripts/smoke-test-phase12.sh"
echo "================================================================"
