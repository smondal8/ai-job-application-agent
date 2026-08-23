# AI Job Application Agent — Operations & API Reference Guide

This operational manual documents how to start, stop, monitor, and interact with the **AI Job Application Agent** services, including detailed API endpoints, health probes, Candidate Profile endpoints, Normalized Job Database endpoints, Source-Agnostic Job Discovery endpoints, and Local LLM (Ollama) JD Analysis & Resume Tailoring.

---

## 1. Service Lifecycle Management (Start, Stop, Restart)

The system consists of two primary services:
1. **Backend**: Python 3.12+ FastAPI server (Default: `http://127.0.0.1:8000`)
2. **Frontend**: React + TypeScript Vite dashboard (Default: `http://127.0.0.1:5173`)
3. **Local LLM**: Ollama daemon on Apple Silicon GPU (Default: `http://127.0.0.1:11434`, Model: `qwen3:8b`)

### A. Quick Commands

| Action | Makefile Alias | Shell Script Command |
| :--- | :--- | :--- |
| **Initial Setup** | `make setup` | `./scripts/setup.sh` |
| **Run Backend** | `make run-backend` | `./scripts/run_backend.sh` |
| **Run Frontend** | `make run-frontend` | `./scripts/run_frontend.sh` |
| **Stop All Services** | `make stop` | `./scripts/stop.sh` |
| **Run All Tests** | `make test` | `./scripts/test.sh` |
| **Apply DB Migrations** | `make migrate` | `./scripts/migrate.sh` |

---

### B. Interactive Mode (Development / Foreground)

Open two terminal tabs:

**Terminal 1 — Start Backend:**
```bash
./scripts/run_backend.sh
# Press Ctrl+C to stop
```

**Terminal 2 — Start Frontend:**
```bash
./scripts/run_frontend.sh
# Press Ctrl+C to stop
```

---

### C. Background / Daemon Mode

To run both services in the background:

**1. Start Backend in Background:**
```bash
source .venv/bin/activate
cd backend
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
echo $! > backend.pid
```

**2. Start Frontend in Background:**
```bash
cd frontend
nohup npm run dev -- --host 127.0.0.1 --port 5173 > frontend.log 2>&1 &
echo $! > frontend.pid
```

**3. Stop All Services:**
```bash
make stop
# OR
./scripts/stop.sh
```

---

## 2. API Endpoints & Diagnostic Reference

All API responses include standard headers:
- `X-Request-ID`: Unique correlation tracking ID (e.g. `req-a1b2c3d4e5f6`).
- `X-Response-Time-Ms`: Backend roundtrip latency in milliseconds.

---

### A. Health & Readiness Probes

#### 1. Full System Health (`GET /health` or `GET /api/v1/health`)
Evaluates database roundtrip query latency, SQLite WAL file accessibility, and storage health.

```bash
curl -X GET http://127.0.0.1:8000/health
```

#### 2. Liveness Probe (`GET /health/live`)
```bash
curl -X GET http://127.0.0.1:8000/health/live
```

#### 3. Readiness Probe (`GET /health/ready`)
```bash
curl -X GET http://127.0.0.1:8000/health/ready
```

---

### B. Phase 5: Local LLM JD Analysis & Resume Tailoring (Ollama `qwen3:8b`)

#### 1. Check Local LLM Status (`GET /api/v1/llm/status`)
Checks connectivity to local Ollama server, verifies `qwen3:8b` model availability, and measures inference latency.

```bash
curl -X GET http://127.0.0.1:8000/api/v1/llm/status
```

#### 2. Analyze Job Description (`POST /api/v1/jobs/{job_id}/analyze`)
Analyzes job requirements against verified candidate profile facts without hallucination.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs/1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "custom_instructions": "Focus evaluation on distributed consensus experience"
  }'
```

#### 3. Get Job Analysis (`GET /api/v1/jobs/{job_id}/analysis`)
```bash
curl -X GET http://127.0.0.1:8000/api/v1/jobs/1/analysis
```

#### 4. Tailor Resume & Cover Letter (`POST /api/v1/jobs/{job_id}/tailor`)
Synthesizes a tailored executive summary, prioritized experience highlights, persuasive cover letter, and complete ATS Markdown resume grounded strictly in verified profile facts.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs/1/tailor \
  -H "Content-Type: application/json" \
  -d '{
    "tone": "professional",
    "custom_instructions": "Emphasize high-throughput distributed database architecture"
  }'
```

#### 5. Get Tailored Resume for Job (`GET /api/v1/jobs/{job_id}/tailored-resume`)
```bash
curl -X GET http://127.0.0.1:8000/api/v1/jobs/1/tailored-resume
```

#### 6. List All Tailored Resumes (`GET /api/v1/tailored-resumes`)
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/tailored-resumes?page=1&page_size=20"
```

---

### C. Phase 4: Source-Agnostic Job Discovery Framework & Orchestration

#### 1. List Registered Adapters (`GET /api/v1/discovery/adapters`)
```bash
curl -X GET http://127.0.0.1:8000/api/v1/discovery/adapters
```

#### 2. Launch Discovery Run (`POST /api/v1/discovery/run`)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/discovery/run \
  -H "Content-Type: application/json" \
  -d '{
    "criteria": {
      "keywords": ["Distributed Systems", "Backend Engineer"],
      "target_companies": ["stripe", "openai", "anthropic", "figma"],
      "locations": ["San Francisco, CA", "Remote"],
      "remote_only": false,
      "sources": ["greenhouse", "lever", "remote_tech", "protected_portal_fallback"],
      "max_results_per_source": 25
    }
  }'
```

#### 3. List Discovery Runs (`GET /api/v1/discovery/runs`)
```bash
curl -X GET http://127.0.0.1:8000/api/v1/discovery/runs
```

---

### D. Phase 3: Normalized Job Database & Ingestion Endpoints

#### 1. List & Filter Normalized Jobs (`GET /api/v1/jobs`)
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/jobs?remote_type=remote&seniority_level=senior&page=1&page_size=20"
```

#### 2. Ingest Jobs via JSON (`POST /api/v1/jobs/ingest/json`)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs/ingest/json \
  -H "Content-Type: application/json" \
  -d '{
    "jobs": [
      {
        "title": "Staff Platform Engineer",
        "company": "Stripe, Inc.",
        "location": "San Francisco, CA",
        "remote_type": "hybrid",
        "salary_min": 190000,
        "salary_max": 250000
      }
    ],
    "source": "json_feed"
  }'
```

#### 3. Ingest Jobs via CSV (`POST /api/v1/jobs/ingest/csv`)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs/ingest/csv \
  -H "Content-Type: application/json" \
  -d '{
    "csv_text": "job_title,employer,location,remote_type\nSenior SRE,Cloudflare,Remote,remote",
    "source": "csv_feed"
  }'
```

---

### E. Phase 2: Candidate Profile & Ground Truth Endpoints

#### 1. Primary Candidate Profile (`GET /api/v1/profile`)
```bash
curl -X GET http://127.0.0.1:8000/api/v1/profile
```

#### 2. Authoritative LLM Ground Truth Context (`GET /api/v1/profile/{id}/verified-context`)
Strictly returns ONLY facts where `is_verified == True`.

```bash
curl -X GET http://127.0.0.1:8000/api/v1/profile/1/verified-context
```

---

### F. Interactive Documentation UIs

- **Swagger UI (OpenAPI Interactive Explorer)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema Specification (JSON)**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 3. Database Management & Migrations

Database files and migrations are managed via **Alembic**:

```bash
# Run latest database migrations (Applies 0001, 0002, 0003, 0004, and 0005)
make migrate
# OR: ./scripts/migrate.sh

# Inspect current migration version
source .venv/bin/activate
cd backend && alembic current
```
