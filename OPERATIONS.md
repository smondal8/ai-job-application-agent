# AI Job Application Agent — Operations & API Reference Guide

This operational manual documents how to start, stop, monitor, and interact with the **AI Job Application Agent** services, including detailed API endpoints, health probes, Candidate Profile & Master Resume endpoints, and error contract specifications.

---

## 1. Service Lifecycle Management (Start, Stop, Restart)

The system consists of two primary services:
1. **Backend**: Python 3.12+ FastAPI server (Default: `http://127.0.0.1:8000`)
2. **Frontend**: React + TypeScript Vite dashboard (Default: `http://127.0.0.1:5173`)

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

**3. Check Status:**
```bash
# Check if backend responds
curl -s http://127.0.0.1:8000/health/live

# Check listening ports
lsof -i :8000
lsof -i :5173
```

**4. Stop All Services:**
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
Evaluates the entire backend subsystem, including database roundtrip query latency, SQLite WAL file accessibility, and local storage write probe.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/health
```

#### 2. Liveness Probe (`GET /health/live`)
Ultra-lightweight ping probe for load balancers and process orchestrators to verify the process is alive without querying the database.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/health/live
```

#### 3. Readiness Probe (`GET /health/ready`)
Traffic gating probe. Returns `HTTP 200 OK` if the database is reachable and storage is writable; otherwise returns `HTTP 503 Service Unavailable`.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/health/ready
```

---

### B. Phase 2: Candidate Profile & Ground Truth Endpoints

#### 1. Primary Candidate Profile (`GET /api/v1/profile`)
Retrieves the active candidate master profile including nested work experiences, educations, candidate skills, and projects.

```bash
curl -X GET http://127.0.0.1:8000/api/v1/profile
```

#### 2. Update Candidate Profile Basics (`PUT /api/v1/profile/{id}`)
Update candidate legal name, headline, summary, contact details, and social links.

```bash
curl -X PUT http://127.0.0.1:8000/api/v1/profile/1 \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alex Morgan",
    "email": "alex.morgan@example.com",
    "headline": "Senior AI Systems Architect",
    "location": "San Francisco, CA"
  }'
```

#### 3. Human Verification Gate (`POST /api/v1/profile/{id}/verify`)
Approves and locks candidate facts as verified ground truth.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/profile/1/verify?verify_all_children=true"
```

#### 4. Authoritative LLM Ground Truth Context (`GET /api/v1/profile/{id}/verified-context`)
**CRITICAL SERVICE BOUNDARY FOR DOWNSTREAM AI MODULES**:
Strictly returns ONLY facts where `is_verified == True`. Unverified draft facts are completely excluded. Missing fields remain omitted without hallucination.

```bash
curl -X GET http://127.0.0.1:8000/api/v1/profile/1/verified-context
```

**Response Payload (`200 OK`):**
```json
{
  "profile_id": 1,
  "profile_verified": true,
  "verified_at": "2026-08-23T14:20:00+00:00",
  "candidate": {
    "full_name": "Alex Morgan",
    "email": "alex.morgan@example.com",
    "phone": "+1 (555) 019-2834",
    "location": "San Francisco, CA",
    "headline": "Senior AI Systems Architect",
    "summary": "Distributed systems engineer specializing in LLM agents."
  },
  "experiences": [
    {
      "id": 1,
      "company": "DeepMind",
      "position": "Research Engineer",
      "start_date": "2022-01",
      "end_date": null,
      "is_current": true,
      "highlights": ["Architected autonomous multi-agent systems."]
    }
  ],
  "educations": [],
  "skills": [
    {"name": "Python", "category": "languages", "proficiency": "expert"},
    {"name": "FastAPI", "category": "frameworks", "proficiency": "advanced"}
  ],
  "projects": [],
  "stats": {
    "verified_experiences_count": 1,
    "verified_educations_count": 0,
    "verified_skills_count": 2,
    "verified_projects_count": 0,
    "total_verified_facts": 4
  },
  "formatted_llm_prompt_context": "# AUTHORITATIVE CANDIDATE GROUND TRUTH (VERIFIED FACTS ONLY)\n**Candidate Name**: Alex Morgan\n..."
}
```

---

### C. Phase 2: Raw Resume Ingestion & Storage

#### 1. Ingest Raw Pasted Resume Text (`POST /api/v1/resumes/imports/text`)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/resumes/imports/text \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Alex Morgan\nalex@example.com\nSkills: Python, FastAPI, Docker",
    "label": "Imported Resume 2026"
  }'
```

#### 2. Upload Raw Resume File (`POST /api/v1/resumes/imports/upload`)
Securely stores uploaded file in `./data/storage/resumes/` (never in Git), computes SHA-256 integrity hash, and parses draft candidate facts.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/resumes/imports/upload \
  -F "file=@/path/to/resume.pdf"
```

#### 3. Transfer Draft Facts to Profile (`POST /api/v1/resumes/imports/{id}/apply-to-profile`)
Transfers extracted draft facts into candidate profile entities with `is_verified: False` for human review.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/resumes/imports/1/apply-to-profile
```

---

### D. Interactive Documentation UIs

- **Swagger UI (OpenAPI Interactive Explorer)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema Specification (JSON)**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 3. Database Management & Migrations

Database files and migrations are managed via **Alembic**:

```bash
# Run latest database migrations (Applies 0001 and 0002)
make migrate
# OR: ./scripts/migrate.sh

# Inspect current migration version
source .venv/bin/activate
cd backend && alembic current
```
