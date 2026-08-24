# AI Job Application Agent — Setup & Operations Guide (v1.0.0)

This guide provides end-to-end instructions for installing, configuring, running, and maintaining the AI Job Application Agent in a production-ready local environment.

---

## 1. Prerequisites & System Requirements

- **Operating System**: macOS (Apple Silicon M1/M2/M3/M4 recommended for GPU acceleration) or Linux (Ubuntu 22.04+).
- **Python**: Version 3.12 or higher.
- **Node.js**: Version 18 LTS or higher (with `npm`).
- **Local LLM Engine**: [Ollama](https://ollama.com/) running model `qwen3:8b`.
- **Browser Automation**: Playwright Chromium binaries (`playwright install chromium`).

---

## 2. Fast-Track Automated Setup

The repository includes an automated bootstrapping script that creates the virtual environment, installs backend and frontend packages, downloads Playwright browsers, and runs Alembic migrations:

```bash
# Run automated setup
./scripts/setup.sh
```

---

## 3. Manual Step-by-Step Installation

### 3.1. Clone and Configure Environment
```bash
git clone https://github.com/smondal8/ai-job-application-agent.git
cd ai-job-application-agent

# Create local environment config
cp .env.example .env
```

### 3.2. Setup Python Backend
```bash
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r backend/requirements-dev.txt

# Install Playwright browser binaries
playwright install chromium
```

### 3.3. Setup SQLite Database & Migrations
```bash
cd backend
alembic upgrade head
cd ..
```

### 3.4. Setup React Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### 3.5. Setup & Verify Local Ollama LLM
Ensure Ollama is running with the `qwen3:8b` model:

```bash
# Verify Ollama service
curl -s http://127.0.0.1:11434/api/tags

# Pull the required model if not already present
ollama pull qwen3:8b
```

---

## 4. Starting and Managing Services

### 4.1. Start Backend Server
```bash
# In terminal 1 (starts FastAPI on port 8000)
./scripts/run_backend.sh
```
- **API Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Diagnostics**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 4.2. Start Frontend Dashboard
```bash
# In terminal 2 (starts Vite on port 5173)
./scripts/run_frontend.sh
```
- **Dashboard Interface**: [http://127.0.0.1:5173](http://127.0.0.1:5173)

### 4.3. Stopping All Services
```bash
./scripts/stop.sh
```

---

## 5. Operations & Disaster Recovery Procedures

### 5.1. Creating a Point-in-Time Database & Artifact Snapshot
Backups utilize SQLite's native online backup API to take non-blocking, zero-corruption snapshots accompanied by SHA-256 integrity verification:

```bash
# Create full backup (Database + data/storage/ artifacts)
curl -X POST "http://127.0.0.1:8000/api/v1/system/backups?include_artifacts=true"
```

### 5.2. Listing and Verifying Backups
```bash
# List all snapshots
curl -s "http://127.0.0.1:8000/api/v1/system/backups"

# Cryptographically verify backup integrity
curl -X POST "http://127.0.0.1:8000/api/v1/system/backups/{backup_id}/verify"
```

### 5.3. Restoring from a Verified Backup
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/system/backups/{backup_id}/restore"
```

### 5.4. Crash Recovery & Orphan Task Reconciliation
If background tasks are interrupted due to process crash, network failure, or reboot:

```bash
# Reconcile tasks older than 15 minutes into failed state with audit logs
curl -X POST "http://127.0.0.1:8000/api/v1/system/recover-stale?max_age_minutes=15"
```

---

## 6. Running the Complete Verification Test Suite

To run all 130 unit, integration, and security regression tests:

```bash
./scripts/test.sh
```

To run the full end-to-end smoke test:
```bash
./scripts/smoke-test-phase12.sh
```
