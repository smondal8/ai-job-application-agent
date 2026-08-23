from app.core.config import Settings, get_settings


def test_settings_initialization():
    settings = get_settings()
    assert settings.APP_NAME == "AI Job Application Agent"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.ENVIRONMENT == "testing"
    assert settings.is_sqlite is True


def test_settings_public_config():
    settings = get_settings()
    public_config = settings.get_public_config()

    assert "app_name" in public_config
    assert "app_version" in public_config
    assert "pipeline_stages" in public_config
    assert len(public_config["pipeline_stages"]) == 6

    # Verify Phase 1 is ready and active
    phase1 = public_config["pipeline_stages"][0]
    assert phase1["stage_id"] == "core_foundation"
    assert phase1["status"] == "ready"
    assert phase1["active"] is True

    # Verify Phase 2 is planned
    phase2 = public_config["pipeline_stages"][1]
    assert phase2["stage_id"] == "job_discovery"
    assert phase2["status"] == "planned"
    assert phase2["active"] is False


def test_sqlite_db_path_handling():
    settings = Settings(DATABASE_URL="sqlite:///./custom_data/custom.db")
    assert settings.is_sqlite is True
    assert settings.sqlite_db_path is not None
    assert str(settings.sqlite_db_path).endswith("custom.db")

    memory_settings = Settings(DATABASE_URL="sqlite:///:memory:")
    assert memory_settings.sqlite_db_path is None
