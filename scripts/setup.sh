#!/usr/bin/env bash
set -e

echo "================================================================"
echo "AI Job Application Agent - Environment Setup"
echo "================================================================"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# 1. Check Python version
echo "[1/5] Checking Python 3.12+ requirement..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 could not be found. Please install Python 3.12+."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Detected Python: $PYTHON_VERSION"

# 2. Check Node & NPM
echo "[2/5] Checking Node.js and NPM..."
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm could not be found. Please install Node.js."
    exit 1
fi
echo "Detected Node: $(node --version), NPM: $(npm --version)"

# 3. Setup .env file
if [ ! -f .env ]; then
    echo "[3/5] Initializing .env from .env.example..."
    cp .env.example .env
else
    echo "[3/5] Existing .env file found."
fi

# 4. Setup Python Virtual Environment and install dependencies
echo "[4/5] Setting up virtual environment (.venv) & installing backend dependencies..."
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements-dev.txt

# 5. Setup Frontend dependencies
echo "[5/5] Installing frontend dependencies & building static bundle..."
cd "$ROOT_DIR/frontend"
npm install
npm run build

cd "$ROOT_DIR/backend"
echo "Running database migrations with Alembic..."
alembic upgrade head

echo ""
echo "================================================================"
echo " Setup Completed Successfully!"
echo " - To run backend:  ./scripts/run_backend.sh"
echo " - To run frontend: ./scripts/run_frontend.sh"
echo " - To run tests:    ./scripts/test.sh"
echo "================================================================"
