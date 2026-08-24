from functools import lru_cache
import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment and .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # App meta
    APP_NAME: str = "AI Job Application Agent"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./data/job_agent.db"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Structured Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"  # "console" | "json"

    # Local Storage Directory
    STORAGE_DIR: str = "./data/storage"

    # Local LLM Subsystem (Ollama on Apple Silicon GPU)
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_TIMEOUT_SECONDS: float = 120.0
    OLLAMA_TEMPERATURE: float = 0.1

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def sqlite_db_path(self) -> Optional[Path]:
        if not self.is_sqlite:
            return None
        raw_path = self.DATABASE_URL.replace("sqlite:///", "")
        if raw_path == ":memory:":
            return None
        return Path(raw_path).resolve()

    def ensure_directories(self) -> None:
        """Ensure necessary storage and database directories exist."""
        storage_path = Path(self.STORAGE_DIR)
        storage_path.mkdir(parents=True, exist_ok=True)

        if self.is_sqlite:
            db_path = self.sqlite_db_path
            if db_path and db_path.parent:
                db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_public_config(self) -> dict:
        """Return safe, sanitized configuration for status and UI display."""
        return {
            "app_name": self.APP_NAME,
            "app_version": self.APP_VERSION,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "api_v1_prefix": self.API_V1_STR,
            "database_type": "sqlite" if self.is_sqlite else "other",
            "storage_dir": self.STORAGE_DIR,
            "log_level": self.LOG_LEVEL,
            "log_format": self.LOG_FORMAT,
            "llm_provider": "ollama",
            "llm_model": self.OLLAMA_MODEL,
            "llm_base_url": self.OLLAMA_BASE_URL,
            "pipeline_stages": [
                {
                    "stage_id": "core_foundation",
                    "name": "Phase 1: Foundation & Core Infrastructure",
                    "status": "ready",
                    "description": "FastAPI backend, SQLite DB, React dashboard, error contract, health checks",
                    "active": True,
                },
                {
                    "stage_id": "candidate_profile",
                    "name": "Phase 2: Candidate Profile & Master Resume",
                    "status": "ready",
                    "description": "Verified candidate facts, master resume subsystem, untrusted parser & LLM ground truth boundary",
                    "active": True,
                },
                {
                    "stage_id": "job_database",
                    "name": "Phase 3: Normalized Job DB & Ingestion",
                    "status": "ready",
                    "description": "Normalized job catalog, company registry, JSON/CSV ingestion fixtures, deterministic deduplication",
                    "active": True,
                },
                {
                    "stage_id": "job_discovery",
                    "name": "Phase 4: Job Discovery & Orchestration",
                    "status": "ready",
                    "description": "Source-agnostic adapter framework, rate limits, retries, Greenhouse/Lever/Remote feeds, and discovery run orchestration",
                    "active": True,
                },
                {
                    "stage_id": "jd_analysis_matching",
                    "name": "Phase 5: Structured JD Analysis & Candidate Matching",
                    "status": "ready",
                    "description": "Structured output pipeline via local Ollama (qwen3:8b) for untrusted JD analysis, deterministic + semantic skill matching, and objective fit scoring",
                    "active": True,
                },
                {
                    "stage_id": "resume_tailoring",
                    "name": "Phase 6: Grounded Resume Tailoring & Document Compilation",
                    "status": "ready",
                    "description": "Grounded resume and cover letter tailoring with atomic source fact traceability, strict claim validation, and deterministic document compilation",
                    "active": True,
                },
                {
                    "stage_id": "application_dashboard",
                    "name": "Phase 7: Central Application Dashboard & Review Workflow",
                    "status": "ready",
                    "description": "Central application management, job & tailored resume linking, application read/review workflows, and comprehensive application dossier dashboard",
                    "active": True,
                },
                {
                    "stage_id": "approval_and_submission",
                    "name": "Phase 8: Human Approval Security Boundary & State Machine",
                    "status": "ready",
                    "description": "Cryptographic human approval gate bound to immutable material inputs (job, candidate, tailored resume, screening answers), strict state machine enforcement, and preparation authorization",
                    "active": True,
                },
                {
                    "stage_id": "browser_automation_staging",
                    "name": "Phase 9: Playwright Browser Application-Preparation Engine",
                    "status": "ready",
                    "description": "Playwright-based browser application preparation engine, generic adapter framework, strict server-side approval authorization verification, automated form pre-filling, screenshot capture, and non-negotiable final submission safety guards",
                    "active": True,
                },
                {
                    "stage_id": "portal_adapters_staging",
                    "name": "Phase 10: Portal-Specific Adapters & Robust Assisted Staging",
                    "status": "ready",
                    "description": "Isolated portal-specific Playwright adapters (Greenhouse, Lever, Ashby, Workday, Generic), layout change resilience, screening answer mapping, global safety guard enforcement, and automated human handoff",
                    "active": True,
                },
            ],
        }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
