# AI Job Application Agent — End-to-End System Architecture (v1.0.0)

## 1. Architectural Vision & Core Invariants

The **AI Job Application Agent** is an autonomous, local-first job search, analysis, resume tailoring, and assisted application staging platform. Engineered around strict human-in-the-loop security boundaries, the system ensures complete privacy, zero hallucinations, and total candidate control.

```
+----------------------------------------------------------------------------------------------------+
|                                    12-Stage Pipeline Architecture                                  |
|                                                                                                    |
|  [01: Foundation]       [02: Verified Profile]    [03: Job Catalog]       [04: Job Discovery]      |
|  FastAPI + SQLite WAL   Master Facts & Ground     Deduplication Engine    Greenhouse / Lever /     |
|  Error RFC-7807         Truth Isolation Boundary  Company Normalization   Remote API Feeds         |
|         │                         │                        │                       │               |
|         ▼                         ▼                        ▼                       ▼               |
|  [05: Match Studio]     [06: Grounded Tailor]     [07: Dossier Dashboard] [08: Approval Gate]      |
|  Ollama (qwen3:8b)      Atomic Fact Traceability  Central Application     Cryptographic Hash       |
|  Semantic + Hard Match  Strict Claim Validator    Review & Staging UI     Material Input Binding   |
|         │                         │                        │                       │               |
|         ▼                         ▼                        ▼                       ▼               |
|  [09: Browser Staging]  [10: Portal Adapters]     [11: Hardening & Recov] [12: E2E Stabilization]  |
|  Playwright Automation  Greenhouse / Lever /      Idempotency / Redact    Complete Test Suite      |
|  Assisted Form Pre-Fill Ashby / Workday / Generic Disaster Backup & Metric 130 Verified Tests      |
|  (SUBMIT GUARD ACTIVE)  Layout Resilience Guards  PRAGMA Check & Recovery Production Runbooks      |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Phase-by-Phase Architectural Breakdown

### Phase 1: Foundation & Core Infrastructure
- **Framework**: FastAPI (Python 3.12+ async server), SQLite in WAL mode with connection pooling.
- **Error Handling**: Standardized RFC-7807 compliant error envelope (`APIErrorResponse`, `ErrorBody`).
- **Telemetry**: Contextual `Request-ID` correlation across console and JSON logging formats.
- **Health Probes**: Liveness (`/health/live`), readiness (`/health/ready`), and detailed system health (`/health`).

### Phase 2: Candidate Profile & Ground Truth Isolation
- **Domain**: Atomic fact model separating candidate profile (`CandidateProfile`), work experience (`WorkExperience`), education (`Education`), skills (`CandidateSkill`), and projects (`Project`).
- **Ground Truth Isolation**: The LLM is only permitted to read verified atomic facts. Untrusted raw resume imports are isolated in `RawResumeImport`.

### Phase 3: Normalized Job Database & Deduplication
- **Catalog**: Canonical `Job` entity, `Company` registry, and ingestion batches (`JobIngestionBatch`).
- **Deterministic Deduplication**: Computes SHA-256 hash over normalized `(title, company, clean_description)` to block duplicate postings across discovery sources.

### Phase 4: Job Discovery Framework & Orchestrator
- **Adapters**: Source-agnostic adapters (`GreenhouseAdapter`, `LeverAdapter`, `RemoteFeedAdapter`, `ManualEntryAdapter`).
- **Orchestration**: Rate limiting, retry backoff with jitter, error containment, and execution ledger in `JobDiscoveryRun`.

### Phase 5: Structured JD Analysis & Candidate Matching
- **Local LLM Engine**: Local Ollama running `qwen3:8b` on Apple Silicon GPU with zero cloud LLM dependencies.
- **Untrusted JD Containment**: Prompts explicitly wrap job descriptions inside boundary markers and treat text as untrusted data.
- **Objective Fit Scoring**: Hybrid scoring engine combining deterministic keyword/skill matching with local LLM semantic analysis.

### Phase 6: Grounded Resume Tailoring & Document Compilation
- **Atomic Traceability**: Tailored resume bullet points and cover letter claims require explicit `source_fact_ids` mapped to verified candidate facts.
- **Claim Validation**: `TraceabilityValidator` rejects ungrounded hallucinations or flags them for human review (`requires_human_review`).
- **Deterministic Compilation**: Generates Markdown, Plaintext, and HTML documents deterministically.

### Phase 7: Central Application Dashboard & Review Workflow
- **State Machine**: Central `Application` entity linked to exactly one `Job` and selected `TailoredResume`.
- **Review Workflow**: Unified dossier interface displaying job parameters, fit analysis, verified facts, tailored resume diffs, and review history (`ApplicationReview`).

### Phase 8: Human Approval Security Boundary & State Machine
- **Cryptographic Gate**: Server-side authorization gate (`ApprovalService`) binding human approval to exact SHA-256 hashes of material inputs:
  $$\text{Approval Token} = \text{HMAC-SHA256}(\text{Job Hash}, \text{Candidate Hash}, \text{Resume Hash}, \text{Answers Hash})$$
- **Automatic Invalidation**: If any material input changes after approval, the approval certificate is immediately invalidated (`requires_reapproval`), blocking all browser preparation.

### Phase 9: Playwright Browser Application Preparation Engine
- **Engine**: Headless and headed Chromium automation using Playwright.
- **Non-Negotiable Submit Guard**: Pre-fills application forms, uploads approved resume documents, maps screening answers, captures visual audit screenshots, and strictly halts before the final submit button (`final_submit_clicked = False`).

### Phase 10: Portal-Specific Adapters & Robust Assisted Staging
- **Portal Adapters**: Isolated adapters for major ATS platforms:
  - `GreenhousePreparationAdapter` (standard forms and iframe embeds)
  - `LeverPreparationAdapter` (multi-section application portals)
  - `AshbyPreparationAdapter` (React SPA question flows)
  - `WorkdayPreparationAdapter` (multi-step wizard flows)
  - `GenericPortalPreparationAdapter` (heuristic fallback)
- **Safety Intercept**: Detects CAPTCHA challenges, authentication walls, or unknown complex questions and safely pauses for human takeover (`blocked_by_captcha`, `paused_for_human_input`).

### Phase 11: Application Hardening, Observability, Resilience & Disaster Recovery
- **Untrusted Input Security Guard**: `ApplicationSecurityGuard` prevents LLM outputs from overriding approvals or altering security boundaries.
- **Sensitive Data Redaction**: Automatic regex masking of Bearer tokens, API keys (`sk-...`, `ghp_...`), passwords, SSNs, and credit cards in logs and payloads.
- **Idempotency & Replay Cache**: `IdempotencyService` enforces unique keys and prevents duplicate mutations.
- **Disaster Recovery & Snapshots**: Online SQLite point-in-time snapshots verified with `PRAGMA integrity_check`, SHA-256 validation, and artifact tarballs.
- **Crash Recovery**: Auto-reconciliation of orphaned discovery and staging background tasks.

### Phase 12: Complete System Stabilization & E2E Verification
- **E2E Verification**: Full end-to-end integration pipeline verified with controlled local HTML fixtures.
- **Negative Security Suite**: Proves approval requirements, hash invalidation on tampering, challenge pauses, and permanent submit guard enforcement.
- **Operations & Runbooks**: Comprehensive deployment, troubleshooting, and operations documentation.

---

## 3. Database Schema Overview

```
                      +------------------+
                      | CandidateProfile |
                      +--------+---------+
                               │ 1:N
        +----------------------+----------------------+
        │                      │                      │
+-------▼--------+     +-------▼--------+     +-------▼--------+
| WorkExperience |     |   Education    |     | CandidateSkill |
+----------------+     +----------------+     +----------------+
                               │ 1:N
                               ▼
                        +--------------+
                        | TailoredResume|
                        +-------+------+
                                │ 1:N
+---------------+               │
|      Job      |               │
+-------+-------+               │
        │ 1:N                   │
        ▼                       ▼
+--------------------------------------+
|             Application              |
+-------------------+------------------+
                    │ 1:1
                    ▼
+--------------------------------------+
|         ApplicationApproval          |
+-------------------+------------------+
                    │ 1:N
                    ▼
+--------------------------------------+
|        BrowserPreparationRun         |
+--------------------------------------+
```
