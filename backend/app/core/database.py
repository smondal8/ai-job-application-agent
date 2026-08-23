import time
from typing import Any, Dict, Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("app.database")
settings = get_settings()

# Engine configuration
connect_args: Dict[str, Any] = {}
if settings.is_sqlite:
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG and settings.LOG_LEVEL == "DEBUG",
    pool_pre_ping=True,
)


# SQLite PRAGMA configuration for data integrity and performance
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.is_sqlite:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
        except Exception as e:
            logger.warning("Failed setting SQLite pragma: %s", e)
        finally:
            cursor.close()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> Dict[str, Any]:
    """Test the database connectivity and compute round-trip latency."""
    start_time = time.perf_counter()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            db_path = str(settings.sqlite_db_path) if settings.sqlite_db_path else "in-memory"
            return {
                "status": "healthy",
                "connected": True,
                "latency_ms": latency_ms,
                "dialect": engine.dialect.name,
                "database_target": db_path,
                "query_result": result,
            }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error("Database health check failed: %s", exc)
        return {
            "status": "unhealthy",
            "connected": False,
            "latency_ms": latency_ms,
            "dialect": engine.dialect.name if hasattr(engine, "dialect") else "unknown",
            "error": str(exc),
        }
