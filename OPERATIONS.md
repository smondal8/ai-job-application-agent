# AI Job Application Agent — Operations & API Reference Guide

This operational manual documents how to start, stop, monitor, and interact with the **AI Job Application Agent (Phase 1)** services, including detailed API endpoints, health probes, and error contract specifications.

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

Alternatively, kill by process name or port:
```bash
# Graceful stop by port
kill $(lsof -t -i :8000) 2>/dev/null || true
kill $(lsof -t -i :5173) 2>/dev/null || true
```

---

## 2. API Endpoints & Health Diagnostic Reference

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

**Response (`200 OK`):**
```json
{
  "status": "healthy",
  "timestamp": "2026-08-23T13:18:09.835083+00:00",
  "version": "0.1.0",
  "uptime_seconds": 128.45,
  "environment": "development",
  "database": {
    "status": "healthy",
    "connected": true,
    "latency_ms": 0.65,
    "dialect": "sqlite",
    "database_target": "/Users/soumyamondal/repo/ai-job-application-agent/backend/data/job_agent.db",
    "error": null
  },
  "storage": {
    "status": "healthy",
    "storage_dir": "/Users/soumyamondal/repo/ai-job-application-agent/backend/data/storage",
    "writable": true,
    "error": null
  }
}
```

---

#### 2. Liveness Probe (`GET /health/live`)
Ultra-lightweight ping probe for load balancers and process orchestrators to verify the process is alive without querying the database.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/health/live
```

**Response (`200 OK`):**
```json
{
  "status": "alive",
  "timestamp": "2026-08-23T13:18:10.123456+00:00"
}
```

---

#### 3. Readiness Probe (`GET /health/ready`)
Traffic gating probe. Returns `HTTP 200 OK` if the database is reachable and storage is writable; otherwise returns `HTTP 503 Service Unavailable`.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/health/ready
```

**Response (`200 OK`):**
```json
{
  "ready": true,
  "status": "ready",
  "timestamp": "2026-08-23T13:18:10.554321+00:00",
  "checks": {
    "database": true,
    "storage": true
  }
}
```

---

### B. Configuration & Architecture Endpoints

#### 1. System Metadata & Config (`GET /api/v1/config`)
Returns sanitized environment configuration, active database type, storage directory, and feature states.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/api/v1/config
```

**Response (`200 OK`):**
```json
{
  "app_name": "AI Job Application Agent",
  "app_version": "0.1.0",
  "environment": "development",
  "debug": true,
  "api_v1_prefix": "/api/v1",
  "database_type": "sqlite",
  "storage_dir": "./data/storage",
  "log_level": "INFO",
  "log_format": "console",
  "pipeline_stages": [
    {
      "stage_id": "core_foundation",
      "name": "Phase 1: Foundation & Core Infrastructure",
      "status": "ready",
      "description": "FastAPI backend, SQLite DB, React dashboard, error contract, health checks",
      "active": true
    },
    {
      "stage_id": "job_discovery",
      "name": "Phase 2: Job Discovery & Scraping",
      "status": "planned",
      "description": "Job board adapters, scrapers, search query filters",
      "active": false
    }
  ]
}
```

---

#### 2. Pipeline Stages Architecture (`GET /api/v1/pipeline`)
Returns the complete 6-stage sequential pipeline status map.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/api/v1/pipeline
```

---

#### 3. Error Contract Test Lab (`GET /api/v1/test-error`)
Triggers various error types to verify conformity to the unified RFC-7807 error schema.

**Request Examples:**
```bash
# Test 404 Not Found
curl -X GET "http://127.0.0.1:8000/api/v1/test-error?error_type=not_found"

# Test 400 Bad Request
curl -X GET "http://127.0.0.1:8000/api/v1/test-error?error_type=bad_request"

# Test 501 Pipeline Stage Disabled
curl -X GET "http://127.0.0.1:8000/api/v1/test-error?error_type=pipeline_disabled"

# Test 500 Safe Unhandled Exception
curl -X GET "http://127.0.0.1:8000/api/v1/test-error?error_type=unhandled"
```

**Sample Error Response Payload (`404 Not Found`):**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested test entity was not found.",
    "details": {
      "entity": "TestJob",
      "id": 999
    },
    "request_id": "req-9a8b7c6d5e4f",
    "timestamp": "2026-08-23T13:18:18.538799+00:00"
  }
}
```

---

### C. Foundational Data Endpoints

#### 1. Jobs (`/api/v1/jobs`)

- **List Jobs:**
  ```bash
  curl -X GET "http://127.0.0.1:8000/api/v1/jobs?page=1&page_size=10"
  ```
- **Create Job:**
  ```bash
  curl -X POST http://127.0.0.1:8000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d '{
      "title": "Senior AI Systems Engineer",
      "company": "DeepMind",
      "location": "London, UK",
      "remote_type": "hybrid",
      "salary_min": "140000.00",
      "salary_max": "180000.00",
      "currency": "GBP",
      "source": "manual",
      "description_raw": "Seeking senior engineer experienced in LLM agent architectures."
    }'
  ```
- **Get Job Details:**
  ```bash
  curl -X GET http://127.0.0.1:8000/api/v1/jobs/1
  ```
- **Delete Job:**
  ```bash
  curl -X DELETE http://127.0.0.1:8000/api/v1/jobs/1
  ```

---

#### 2. Resumes (`/api/v1/resumes`)

- **List Resumes:**
  ```bash
  curl -X GET http://127.0.0.1:8000/api/v1/resumes
  ```
- **Create Resume Entry:**
  ```bash
  curl -X POST http://127.0.0.1:8000/api/v1/resumes \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Principal Engineer Master Resume",
      "version": "1.0",
      "skills": ["Python", "FastAPI", "React", "TypeScript", "SQLAlchemy", "SQLite"],
      "summary": "Full-stack AI systems engineer specializing in robust agent pipelines.",
      "is_default": true
    }'
  ```

---

#### 3. Applications (`/api/v1/applications`)

- **List Applications:**
  ```bash
  curl -X GET http://127.0.0.1:8000/api/v1/applications
  ```
- **Get Application Details:**
  ```bash
  curl -X GET http://127.0.0.1:8000/api/v1/applications/1
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
# Run latest database migrations
make migrate
# OR: ./scripts/migrate.sh

# Inspect current migration version
source .venv/bin/activate
cd backend && alembic current

# Generate a new migration after editing models
cd backend && alembic revision --autogenerate -m "add_new_feature_columns"
```

---

## 4. Log Inspection & Tracing

Logs include timestamp, level, correlation `request_id`, caller module, and line number:

```
[INFO    ] 2026-08-23 13:18:09 [req-dadccac870b3] app.main:36 - GET /health -> 200 (0.65 ms)
[WARNING ] 2026-08-23 13:18:18 [req-dadccac870b3] app.errors:115 - AppException handled: [RESOURCE_NOT_FOUND] The requested test entity was not found. (status=404)
```

To filter logs by a specific correlation ID:
```bash
grep "req-dadccac870b3" backend.log
```
