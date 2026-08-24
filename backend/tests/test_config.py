from app.core.config import Settings, get_settings


def test_settings_initialization():
    settings = get_settings()
    assert settings.APP_NAME == "AI Job Application Agent"
    assert settings.ENVIRONMENT == "testing"
    assert settings.is_sqlite is True


def test_settings_public_config():
    settings = get_settings()
    public_config = settings.get_public_config()

    assert "app_name" in public_config
    assert "app_version" in public_config
    assert "pipeline_stages" in public_config
    assert len(public_config["pipeline_stages"]) >= 6

    # Verify Phase 1 is ready and active
    phase1 = public_config["pipeline_stages"][0]
    assert phase1["stage_id"] == "core_foundation"
    assert phase1["status"] == "ready"
    assert phase1["active"] is True

    # Verify Phase 2 is ready and active
    phase2 = public_config["pipeline_stages"][1]
    assert phase2["stage_id"] == "candidate_profile"
    assert phase2["status"] == "ready"
    assert phase2["active"] is True

    # Verify Phase 3 is ready and active
    phase3 = public_config["pipeline_stages"][2]
    assert phase3["stage_id"] == "job_database"
    assert phase3["status"] == "ready"
    assert phase3["active"] is True

    # Verify Phase 4 is ready and active
    phase4 = public_config["pipeline_stages"][3]
    assert phase4["stage_id"] == "job_discovery"
    assert phase4["status"] == "ready"
    assert phase4["active"] is True

    # Verify Phase 5 is ready and active
    phase5 = public_config["pipeline_stages"][4]
    assert phase5["stage_id"] == "jd_analysis_matching"
    assert phase5["status"] == "ready"
    assert phase5["active"] is True

    # Verify Phase 6 is ready and active
    phase6 = public_config["pipeline_stages"][5]
    assert phase6["stage_id"] == "resume_tailoring"
    assert phase6["status"] == "ready"
    assert phase6["active"] is True

    # Verify Phase 7 is ready and active
    phase7 = public_config["pipeline_stages"][6]
    assert phase7["stage_id"] == "application_dashboard"
    assert phase7["status"] == "ready"
    assert phase7["active"] is True

    # Verify Phase 8 is planned
    phase8 = public_config["pipeline_stages"][7]
    assert phase8["stage_id"] == "approval_and_submission"
    assert phase8["status"] == "planned"
    assert phase8["active"] is False


def test_sqlite_db_path_handling():
    settings = Settings(DATABASE_URL="sqlite:///./custom_data/custom.db")
    assert settings.is_sqlite is True
    assert settings.sqlite_db_path is not None
    assert str(settings.sqlite_db_path).endswith("custom.db")

    memory_settings = Settings(DATABASE_URL="sqlite:///:memory:")
    assert memory_settings.sqlite_db_path is None
