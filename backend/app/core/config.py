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

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def sqlite_db_path(self) -> Optional[Path]:
        if not self.is_sqlite:
            return None
        # sqlite:///./data/job_agent.db -> ./data/job_agent.db
        # sqlite:///:memory: -> None
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
                    "stage_id": "jd_analysis",
                    "name": "Phase 3: JD Analysis & Match Scoring",
                    "status": "planned",
                    "description": "Skill extraction, keyword alignment, match scoring engine",
                    "active": False,
                },
                {
                    "stage_id": "resume_tailoring",
                    "name": "Phase 4: Resume Tailoring & Generation",
                    "status": "planned",
                    "description": "Dynamic resume tailoring, cover letter generation, PDF compilation",
                    "active": False,
                },
                {
                    "stage_id": "human_approval",
                    "name": "Phase 5: Human-in-the-Loop Approval",
                    "status": "planned",
                    "description": "Application review queue, manual edits, approval state machine",
                    "active": False,
                },
                {
                    "stage_id": "browser_preparation",
                    "name": "Phase 6: Browser Automation & Submission",
                    "status": "planned",
                    "description": "Portal automation, form field preparation, safe submission gate",
                    "active": False,
                },
            ],
        }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
