# AI Job Application Agent

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4+-3178C6.svg)](https://www.typescriptlang.org/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL-003B57.svg)](https://www.sqlite.org/)
[![Phase 1](https://img.shields.io/badge/Phase-1%20Foundation-emerald.svg)](./ARCHITECTURE.md)

An intelligent, autonomous job application agent engineered with a local-first architecture and deterministic human-in-the-loop approval gates.

---

## Phase 1 Scope & Foundation

Phase 1 implements the complete foundational infrastructure and control plane:
- **FastAPI Backend** with Python 3.12+ async server.
- **React + TypeScript + Vite Frontend** diagnostic dashboard.
- **SQLAlchemy 2.0 + Alembic Migrations** targeting local **SQLite (WAL mode)**.
- **Pydantic Settings** environment configuration (`.env`).
- **Structured Logging** with correlation `Request-ID` tracing across requests and logs.
- **Health & Readiness Endpoints** (`/health`, `/health/live`, `/health/ready`).
- **Standardized API Error Contract** (RFC-7807 compliant).
- **Comprehensive Test Suite** (backend `pytest` + frontend `tsc` build).
- **Git-Friendly Local Scripts & Makefile**.

> **Note on Scope**: Phase 1 establishes the foundational infrastructure, data models, and API contracts. Job discovery scraping, JD analysis, resume tailoring, and browser automation will be introduced in subsequent phases as detailed in [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Pipeline Architecture Roadmap

```
Phase 1: Core Foundation & Control Plane (Active)
   ↓
Phase 2: Job Discovery & Scraping (Planned)
   ↓
Phase 3: JD Analysis & Match Scoring (Planned)
   ↓
Phase 4: Resume Tailoring & Generation (Planned)
   ↓
Phase 5: Human-in-the-Loop Review & Approval (Planned)
   ↓
Phase 6: Browser Automation & Submission Gate (Planned)
```

---

## Directory Structure

```
ai-job-application-agent/
├── .env.example              # Environment variables template
├── .gitignore                # Git ignores for Python, Node, Vite, SQLite
├── Makefile                  # Developer shortcuts
├── README.md                 # Project documentation
├── ARCHITECTURE.md           # End-to-end architecture specification
├── backend/
│   ├── pyproject.toml        # Backend package metadata and pytest config
│   ├── requirements.txt      # Production dependencies
│   ├── requirements-dev.txt  # Testing & development dependencies
│   ├── alembic.ini           # Alembic migration configuration
│   ├── alembic/
│   │   ├── env.py            # Alembic runtime environment
│   │   └── versions/         # Migration scripts
│   │       └── 0001_initial_schema.py
│   ├── app/
│   │   ├── main.py           # FastAPI application entrypoint & middleware
│   │   ├── core/
│   │   │   ├── config.py     # Pydantic BaseSettings configuration
│   │   │   ├── database.py   # SQLAlchemy SQLite engine & sessionmaker
│   │   │   ├── errors.py     # Unified API error handlers & contract
│   │   │   └── logging.py    # Structured JSON & console loggers
│   │   ├── models/           # SQLAlchemy ORM models
│   │   │   ├── base.py       # Timestamp mixin & Base declarative
│   │   │   ├── job.py        # Job listing model
│   │   │   ├── analysis.py   # Job analysis & fit score model
│   │   │   ├── resume.py     # Base & tailored resume models
│   │   │   ├── application.py# Application state machine model
│   │   │   ├── approval.py   # Human review record model
│   │   │   └── audit.py      # System audit log model
│   │   ├── schemas/          # Pydantic DTOs & response schemas
│   │   │   ├── common.py     # Envelope & pagination schemas
│   │   │   ├── health.py     # Health diagnostic schemas
│   │   │   ├── config.py     # System config schemas
│   │   │   ├── job.py        # Job schemas
│   │   │   ├── resume.py     # Resume schemas
│   │   │   └── application.py# Application schemas
│   │   └── api/
│   │       ├── router.py     # Top-level API router aggregator
│   │       └── v1/
│   │           ├── health.py # Health & diagnostic endpoints
│   │           ├── config.py # Config, pipeline, & error-lab endpoints
│   │           ├── jobs.py   # Jobs CRUD foundation
│   │           ├── resumes.py# Resumes CRUD foundation
│   │           └── applications.py # Applications foundation
│   └── tests/                # Pytest test suite
│       ├── conftest.py       # TestClient & SQLite fixtures
│       ├── test_api_v1.py    # API endpoints tests
│       ├── test_config.py    # Settings tests
│       ├── test_database.py  # SQLAlchemy models & relational integrity
│       ├── test_errors.py    # Unified error contract tests
│       ├── test_health.py    # Health/liveness/readiness tests
│       └── test_logging.py   # Request ID & log formatting tests
├── frontend/
│   ├── package.json          # React + TypeScript dependencies
│   ├── tsconfig.json         # TypeScript compiler configuration
│   ├── vite.config.ts        # Vite configuration with backend proxy
│   ├── index.html            # Web application entry HTML
│   └── src/
│       ├── main.tsx          # React application root
│       ├── App.tsx           # Dashboard layout & routing
│       ├── index.css         # Dark mode tech design system
│       ├── types/            # TypeScript type definitions
│       ├── services/         # Typed API client
│       └── components/       # Diagnostic & architectural UI components
└── scripts/
    ├── setup.sh              # Local environment bootstrapping
    ├── run_backend.sh        # Starts FastAPI uvicorn backend
    ├── run_frontend.sh       # Starts Vite dev server
    ├── test.sh               # Runs pytest & frontend builds
    └── migrate.sh            # Executes database migrations
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.12 or higher
- Node.js 18+ and npm

### 2. Setup Environment
Run the automated setup script to create `.venv`, install all Python/Node dependencies, and apply migrations:

```bash
make setup
# OR: ./scripts/setup.sh
```

### 3. Run Test Suite
Verify backend tests and frontend TypeScript build:

```bash
make test
# OR: ./scripts/test.sh
```

### 4. Start Applications Locally
In separate terminal tabs:

**Backend (Port 8000):**
```bash
make run-backend
# OR: ./scripts/run_backend.sh
```

**Frontend (Port 5173):**
```bash
make run-frontend
# OR: ./scripts/run_frontend.sh
```

- **Frontend Dashboard**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Full system health check (DB latency, storage write probe, uptime) |
| `GET` | `/health/live` | Liveness probe for process monitoring |
| `GET` | `/health/ready` | Readiness probe for subsystem traffic gating |
| `GET` | `/api/v1/config` | Sanitized system configuration and phase status |
| `GET` | `/api/v1/pipeline` | Detailed breakdown of all 6 architectural pipeline stages |
| `GET` | `/api/v1/test-error` | Interactive tester for the unified API error contract |
| `GET` | `/api/v1/jobs` | Paginated listing of job postings |
| `POST`| `/api/v1/jobs` | Manual creation/import of a job posting |
| `GET` | `/api/v1/jobs/{id}` | Retrieve single job by ID |
| `GET` | `/api/v1/resumes` | Listing of stored candidate resumes |
| `GET` | `/api/v1/applications` | Listing of application pipeline records |
