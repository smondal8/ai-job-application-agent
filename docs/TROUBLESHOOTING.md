# AI Job Application Agent — Troubleshooting & Diagnostics Guide

This document outlines standard diagnostic procedures and resolutions for common issues encountered during local development, testing, and operations.

---

## 1. Local LLM Subsystem Issues (Ollama & Qwen3 8B)

### Problem: `LLMConnectionError: Failed to connect to Ollama at http://127.0.0.1:11434`
- **Cause**: The local Ollama daemon is not running.
- **Diagnostic Command**:
  ```bash
  curl -s http://127.0.0.1:11434/api/tags
  ```
- **Solution**:
  1. Start Ollama:
     ```bash
     ollama serve
     ```
  2. Verify that `qwen3:8b` is pulled:
     ```bash
     ollama list
     # If missing:
     ollama pull qwen3:8b
     ```

### Problem: LLM Timeout on Large Job Descriptions
- **Cause**: Model latency on high context inputs exceeding timeout limit.
- **Solution**: Adjust `OLLAMA_TIMEOUT_SECONDS` in `.env` (default is `120.0` seconds):
  ```ini
  OLLAMA_TIMEOUT_SECONDS=180.0
  ```

---

## 2. Playwright Browser Automation & Staging Issues

### Problem: `Executable doesn't exist at .../ms-playwright/chromium-...`
- **Cause**: Playwright browser binaries were not installed after package installation.
- **Solution**:
  ```bash
  source .venv/bin/activate
  playwright install chromium
  ```

### Problem: Staging Stops at Checkpoint with `status: paused_for_human_input` or `blocked_by_captcha`
- **Explanation**: This is an **intentional safety invariant**.
- When an ATS portal presents a CAPTCHA challenge, login wall, or unsupported custom question, the adapter safely pauses without attempting to bypass security detection or making assumptions.
- **Resolution**: Open the browser window manually, solve the challenge, and complete the final submission directly.

---

## 3. Human Approval Gate & Hash Invalidation

### Problem: `ForbiddenError: Security Authorization Failed. Reason: Approval invalidated due to material changes`
- **Cause**: The application was approved, but one of the material inputs (Job Description, Candidate Profile, Tailored Resume, or Screening Answers) was altered afterwards.
- **Diagnostic API**:
  ```bash
  curl -s "http://127.0.0.1:8000/api/v1/applications/{application_id}/verify-approval"
  ```
- **Output Inspection**:
  The response will list the exact `mismatches` (e.g. `["Tailored resume content modified after approval."]`).
- **Resolution**:
  Re-review the modified dossier and explicitly grant human approval again via `POST /api/v1/applications/{id}/approve`.

---

## 4. SQLite Database & Migration Issues

### Problem: `sqlite3.OperationalError: database is locked`
- **Cause**: Multiple long-running transactions or missing WAL configuration.
- **Solution**:
  The database engine initializes SQLite in **WAL (Write-Ahead Logging)** mode with `timeout=30.0`. If manual locks persist:
  ```bash
  sqlite3 data/job_agent.db "PRAGMA journal_mode=WAL;"
  ```

### Problem: Database Corruption Suspected
- **Diagnostic Command**:
  ```bash
  sqlite3 data/job_agent.db "PRAGMA integrity_check;"
  ```
- **Expected Output**: `ok`. If corrupted, restore from the latest snapshot using `POST /api/v1/system/backups/{id}/restore`.

---

## 5. Idempotency Header Usage

### Header Specification: `X-Idempotency-Key`
When invoking state-altering endpoints (e.g., granting approvals or executing browser preparation runs):
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/applications/1/approve" \
     -H "Content-Type: application/json" \
     -H "X-Idempotency-Key: idemp_app1_v1" \
     -d '{"approver_notes": "Approved for staging"}'
```
- If the request is re-sent with the identical header and payload, the server returns the cached response immediately without creating duplicate database records or re-executing actions.
