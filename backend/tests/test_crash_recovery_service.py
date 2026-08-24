from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models.discovery import JobDiscoveryRun, JobSearchProfile
from app.models.preparation import BrowserPreparationRun
from app.models.job import Job
from app.models.application import Application
from app.models.candidate import CandidateProfile
from app.services.recovery.crash_recovery_service import crash_recovery_service


def test_crash_recovery_reconciles_stale_tasks(db_session: Session):
    old_start = datetime.now(timezone.utc) - timedelta(hours=2)

    # 1. Create a stale running discovery run (started 2 hours ago)
    stale_disc = JobDiscoveryRun(
        run_id="run_stale_test_101",
        source="greenhouse",
        criteria={"keywords": ["Python", "Backend"]},
        status="running",
    )
    db_session.add(stale_disc)
    db_session.commit()
    db_session.query(JobDiscoveryRun).filter(JobDiscoveryRun.id == stale_disc.id).update({"created_at": old_start})
    db_session.commit()

    # 2. Create a stale initialized preparation run
    profile = CandidateProfile(full_name="Grace Hopper", email="grace@navy.mil", is_verified=True)
    db_session.add(profile)
    db_session.commit()

    job = Job(title="Lead Engineer", company="Tech Corp", description_raw="Desc", description_clean="Desc", source="test")
    db_session.add(job)
    db_session.commit()

    app_ent = Application(job_id=job.id, candidate_profile_id=profile.id, status="approved")
    db_session.add(app_ent)
    db_session.commit()

    stale_prep = BrowserPreparationRun(
        application_id=app_ent.id,
        job_id=job.id,
        approval_token="auth_test_123",
        status="initialized",
    )
    db_session.add(stale_prep)
    db_session.commit()
    db_session.query(BrowserPreparationRun).filter(BrowserPreparationRun.id == stale_prep.id).update({"created_at": old_start})
    db_session.commit()

    # Run recovery
    result = crash_recovery_service.reconcile_stale_runs(db=db_session, max_age_minutes=30)

    assert result["reconciled_discovery_runs"] >= 1
    assert result["reconciled_preparation_runs"] >= 1

    # Verify status changed to failed with diagnostic message
    db_session.refresh(stale_disc)
    db_session.refresh(stale_prep)
    assert stale_disc.status == "failed"
    assert any("crash_recovery" in str(l) for l in stale_disc.adapter_logs)
    assert stale_prep.status == "failed"
    assert "crash recovery" in stale_prep.error_message.lower()
