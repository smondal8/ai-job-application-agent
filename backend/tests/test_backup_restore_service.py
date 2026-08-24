import json
import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.candidate import CandidateProfile
from app.services.backup.backup_service import backup_service


def test_backup_creation_verification_and_restore(db_session: Session, tmp_path: Path):
    # 1. Insert seed data into database
    cand = CandidateProfile(full_name="Margaret Hamilton", email="margaret@mit.edu", headline="Director Software Engineering", is_verified=True)
    db_session.add(cand)
    db_session.commit()
    db_session.refresh(cand)

    # 2. Create full backup
    meta = backup_service.create_backup(db=db_session, include_artifacts=True)
    assert meta is not None
    assert "backup_id" in meta
    assert meta["db_sha256"] is not None
    assert meta["db_dialect"] == "sqlite"

    backup_id = meta["backup_id"]

    # 3. List backups
    backups_list = backup_service.list_backups()
    assert any(b["backup_id"] == backup_id for b in backups_list)

    # 4. Verify backup cryptographic integrity
    verification = backup_service.verify_backup(backup_id)
    assert verification["is_valid"] is True
    assert verification["backup_id"] == backup_id

    # 5. Test restore backup
    restore_result = backup_service.restore_backup(backup_id)
    assert restore_result["status"] == "restored"
    assert restore_result["backup_id"] == backup_id


def test_tampered_backup_fails_verification(db_session: Session):
    """Proves that tampering with backed-up database fails integrity verification."""
    meta = backup_service.create_backup(db=db_session, include_artifacts=False)
    backup_id = meta["backup_id"]

    backup_dir = backup_service._get_backup_root() / backup_id
    db_file = backup_dir / meta["db_file"]

    # Tamper with the database file
    with open(db_file, "ab") as f:
        f.write(b"CORRUPTED_BYTES_INJECTION")

    # Verification must report invalid due to checksum mismatch
    verification = backup_service.verify_backup(backup_id)
    assert verification["is_valid"] is False
    assert "checksum mismatch" in verification["reason"].lower()
