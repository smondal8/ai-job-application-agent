import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session

# Set test environment variables prior to importing app components
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["STORAGE_DIR"] = "./data/test_storage"
os.environ["LOG_LEVEL"] = "DEBUG"

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import create_app

# Clear cached settings so environment variables take effect
get_settings.cache_clear()


@pytest.fixture(scope="session")
def test_settings():
    return get_settings()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a clean in-memory SQLite database session for each test."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine, expire_on_commit=False
    )
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a TestClient with database dependency override."""
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
