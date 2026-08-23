from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.services.profile_service import profile_service


def test_audit_logs_record_profile_events_without_leaking_full_text(db_session: Session):
    # 1. Ingest raw resume text
    sensitive_resume_body = "SECRET CONFIDENTIAL CANDIDATE RESUME TEXT NEVER LOG ME FULLY 12345"
    raw_import = profile_service.import_raw_resume_text(
        db_session, raw_text=sensitive_resume_body, label="Confidential Resume"
    )

    # 2. Query AuditLog records
    audit_records = db_session.query(AuditLog).filter(AuditLog.action == "RAW_RESUME_IMPORTED").all()
    assert len(audit_records) >= 1
    last_audit = audit_records[-1]

    # Verify message and payload contain only metadata, NEVER the full raw text
    assert last_audit.stage == "profile_management"
    assert "confidential_resume.txt" in last_audit.message
    assert sensitive_resume_body not in last_audit.message
    assert sensitive_resume_body not in str(last_audit.payload)

    # 3. Verify profile verification creates audit entry
    profile = profile_service.get_or_create_primary_profile(db_session)
    profile_service.verify_profile(db_session, profile.id, verify_all_children=True)

    verify_audits = db_session.query(AuditLog).filter(AuditLog.action == "PROFILE_VERIFIED").all()
    assert len(verify_audits) >= 1
    assert verify_audits[-1].payload["profile_id"] == profile.id
