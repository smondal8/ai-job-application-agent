# AI Job Application Agent (v1.0.0 Production Release)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4+-3178C6.svg)](https://www.typescriptlang.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-45ba4b.svg)](https://playwright.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-qwen3:8b%20GPU-black.svg)](https://ollama.com/)
[![Tests](https://img.shields.io/badge/Tests-130%20Passing-brightgreen.svg)](./scripts/test.sh)
[![Phase 12 Complete](https://img.shields.io/badge/Status-Phase%2012%20Complete%20(v1.0.0)-emerald.svg)](./docs/RELEASE_NOTES_v1.0.0.md)

An intelligent, autonomous job application agent engineered with a **local-first architecture**, **local Ollama LLM execution (`qwen3:8b`)**, and **deterministic cryptographic human-in-the-loop approval gates**.

---

## 📚 Documentation Quick Links
- 📘 **[Architecture Specification (docs/ARCHITECTURE.md)](./docs/ARCHITECTURE.md)**: Technical architecture covering all 12 phases.
- 🛠️ **[Setup & Operations Runbook (docs/SETUP_AND_OPERATIONS.md)](./docs/SETUP_AND_OPERATIONS.md)**: Installation, Ollama configuration, backups/restore, and crash recovery.
- 🔍 **[Troubleshooting & Diagnostics (docs/TROUBLESHOOTING.md)](./docs/TROUBLESHOOTING.md)**: Common failure modes, local LLM diagnostics, and browser staging.
- 🚀 **[Release Notes v1.0.0 (docs/RELEASE_NOTES_v1.0.0.md)](./docs/RELEASE_NOTES_v1.0.0.md)**: Production milestone summary.

---

## 🏗️ 12-Stage Pipeline Architecture

```
[Phase 01: Core Foundation] ──► [Phase 02: Verified Candidate Profile & Atomic Facts]
                                            │
                                            ▼
[Phase 04: Job Discovery]   ◄── [Phase 03: Normalized Job DB & Deduplication]
        │
        ▼
[Phase 05: JD Analysis & Objective Matching (Ollama qwen3:8b)]
        │
        ▼
[Phase 06: Grounded Resume Tailoring & Atomic Fact Traceability]
        │
        ▼
[Phase 07: Central Application Dashboard & Dossier Review]
        │
        ▼
[Phase 08: Cryptographic Human Approval Gate & Material Hash Binding]
        │
        ▼
[Phase 09: Playwright Browser Application Preparation Engine]
        │
        ▼
[Phase 10: Portal-Specific Adapters (Greenhouse, Lever, Ashby, Workday, Generic)]
        │
        ▼
[Phase 11: Application Hardening, Observability, Redaction & Disaster Recovery]
        │
        ▼
[Phase 12: Complete System Stabilization & E2E Verification]
```

---

## 🔒 Security & Non-Negotiable Invariants

1. **Local-First Privacy**: Uses local Ollama (`qwen3:8b`) running on Apple Silicon GPU. Zero cloud LLM dependencies.
2. **Untrusted Input Policy**: Treats all job descriptions, employer messages, and web DOM elements as untrusted.
3. **No LLM Hallucinations**: Tailored resumes and cover letters must reference valid `source_fact_ids` tracing directly to verified candidate facts.
4. **Server-Side Authorization Boundary**: Browser preparation cannot be launched without explicit cryptographic human approval bound to exact SHA-256 hashes.
5. **Non-Negotiable Submit Guard**: Staging engines fill forms, upload resumes, capture screenshots, and strictly halt before the final submit button (`final_submit_clicked = False`).

---

## ⚡ Quickstart

```bash
# 1. Automated environment setup & migrations
./scripts/setup.sh

# 2. Run backend (Port 8000)
./scripts/run_backend.sh

# 3. Run frontend (Port 5173)
./scripts/run_frontend.sh

# 4. Execute test suite (130 tests)
./scripts/test.sh

# 5. Run end-to-end smoke test
./scripts/smoke-test-phase12.sh
```

- **Frontend Dashboard**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Diagnostics**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
