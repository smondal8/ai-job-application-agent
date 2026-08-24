import hashlib
import json
import os
import shutil
import sqlite3
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError, ValidationError
from app.core.logging import get_logger

logger = get_logger("app.services.backup")


class BackupRestoreService:
    """Enterprise-grade database snapshot, artifact bundling, cryptographic verification, and disaster restoration."""

    def __init__(self):
        self.settings = get_settings()

    def _get_backup_root(self) -> Path:
        root = Path(self.settings.DATA_DIR) / "backups"
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Computes SHA-256 checksum of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def create_backup(self, db: Optional[Session] = None, include_artifacts: bool = True) -> Dict[str, Any]:
        """Creates a verified database snapshot and compressed artifact tarball."""
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{timestamp_str}"
        backup_dir = self._get_backup_root() / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        db_path = self.settings.sqlite_db_path
        db_backup_file = None
        db_hash = None

        if db is not None:
            db_backup_file = backup_dir / "database.db"
            try:
                # Extract sqlite3 connection from SQLAlchemy session
                raw_conn = db.connection().connection.driver_connection
                dst_conn = sqlite3.connect(str(db_backup_file))
                with dst_conn:
                    raw_conn.backup(dst_conn)
                dst_conn.close()
            except Exception:
                if db_path and db_path.exists():
                    src_conn = sqlite3.connect(str(db_path))
                    dst_conn = sqlite3.connect(str(db_backup_file))
                    with dst_conn:
                        src_conn.backup(dst_conn)
                    dst_conn.close()
                    src_conn.close()

            if db_backup_file.exists():
                chk_conn = sqlite3.connect(str(db_backup_file))
                cursor = chk_conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                chk_conn.close()
                if not result or result[0] != "ok":
                    raise ValidationError(f"Backup failed SQLite integrity check: {result}")
                db_hash = self.compute_sha256(db_backup_file)

        elif db_path and db_path.exists():
            db_backup_file = backup_dir / "database.db"
            src_conn = sqlite3.connect(str(db_path))
            dst_conn = sqlite3.connect(str(db_backup_file))
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()

            chk_conn = sqlite3.connect(str(db_backup_file))
            cursor = chk_conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            chk_conn.close()
            if not result or result[0] != "ok":
                raise ValidationError(f"Backup failed SQLite integrity check: {result}")

            db_hash = self.compute_sha256(db_backup_file)

        # Artifacts bundle
        artifacts_tar = None
        artifacts_hash = None
        artifacts_count = 0
        storage_path = Path(self.settings.STORAGE_DIR)
        if include_artifacts and storage_path.exists():
            artifacts_tar = backup_dir / "artifacts.tar.gz"
            with tarfile.open(artifacts_tar, "w:gz") as tar:
                for root, _, files in os.walk(storage_path):
                    for file in files:
                        p = Path(root) / file
                        arcname = p.relative_to(storage_path)
                        tar.add(p, arcname=str(arcname))
                        artifacts_count += 1
            artifacts_hash = self.compute_sha256(artifacts_tar)

        metadata = {
            "backup_id": backup_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "db_dialect": "sqlite" if self.settings.is_sqlite else "other",
            "db_file": db_backup_file.name if db_backup_file and db_backup_file.exists() else None,
            "db_sha256": db_hash,
            "db_size_bytes": db_backup_file.stat().st_size if db_backup_file and db_backup_file.exists() else 0,
            "artifacts_file": artifacts_tar.name if artifacts_tar and artifacts_tar.exists() else None,
            "artifacts_sha256": artifacts_hash,
            "artifacts_count": artifacts_count,
            "artifacts_size_bytes": artifacts_tar.stat().st_size if artifacts_tar and artifacts_tar.exists() else 0,
            "app_version": self.settings.APP_VERSION,
        }

        meta_file = backup_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Successfully generated full backup #{backup_id}")
        return metadata

    def list_backups(self) -> List[Dict[str, Any]]:
        """Lists all existing backups and their metadata."""
        root = self._get_backup_root()
        backups: List[Dict[str, Any]] = []
        for d in sorted(root.iterdir(), reverse=True):
            if d.is_dir():
                meta_file = d / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            backups.append(meta)
                    except Exception as e:
                        logger.warning(f"Failed to read backup metadata in {d}: {e}")
        return backups

    def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """Verifies SHA-256 checksums and database integrity of a backup."""
        backup_dir = self._get_backup_root() / backup_id
        if not backup_dir.exists():
            raise NotFoundError(f"Backup '{backup_id}' not found.")

        meta_file = backup_dir / "metadata.json"
        if not meta_file.exists():
            raise ValidationError(f"Backup '{backup_id}' is missing metadata.json.")

        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        if meta.get("db_file"):
            db_file = backup_dir / meta["db_file"]
            if not db_file.exists():
                return {"is_valid": False, "reason": "Database file missing."}
            actual_db_hash = self.compute_sha256(db_file)
            if actual_db_hash != meta.get("db_sha256"):
                return {"is_valid": False, "reason": "Database checksum mismatch."}
            # Test integrity check
            conn = sqlite3.connect(str(db_file))
            c = conn.cursor()
            c.execute("PRAGMA integrity_check")
            res = c.fetchone()
            conn.close()
            if not res or res[0] != "ok":
                return {"is_valid": False, "reason": f"SQLite corruption detected: {res}"}

        if meta.get("artifacts_file"):
            art_file = backup_dir / meta["artifacts_file"]
            if not art_file.exists():
                return {"is_valid": False, "reason": "Artifacts archive missing."}
            actual_art_hash = self.compute_sha256(art_file)
            if actual_art_hash != meta.get("artifacts_sha256"):
                return {"is_valid": False, "reason": "Artifacts archive checksum mismatch."}

        return {
            "is_valid": True,
            "backup_id": backup_id,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "metadata": meta,
        }

    def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """Restores active database and artifacts from a verified backup."""
        verification = self.verify_backup(backup_id)
        if not verification.get("is_valid"):
            raise ValidationError(f"Cannot restore invalid backup: {verification.get('reason')}")

        meta = verification["metadata"]
        backup_dir = self._get_backup_root() / backup_id

        # 1. Restore SQLite Database
        if meta.get("db_file") and self.settings.sqlite_db_path:
            db_backup_file = backup_dir / meta["db_file"]
            target_path = self.settings.sqlite_db_path
            src_conn = sqlite3.connect(str(db_backup_file))
            dst_conn = sqlite3.connect(str(target_path))
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()
            logger.info(f"Restored SQLite database from backup #{backup_id}")

        # 2. Restore Artifacts
        storage_path = Path(self.settings.STORAGE_DIR)
        if meta.get("artifacts_file") and (backup_dir / meta["artifacts_file"]).exists():
            art_tar = backup_dir / meta["artifacts_file"]
            storage_path.mkdir(parents=True, exist_ok=True)
            with tarfile.open(art_tar, "r:gz") as tar:
                tar.extractall(path=str(storage_path))
            logger.info(f"Restored {meta.get('artifacts_count', 0)} artifacts from backup #{backup_id}")

        return {
            "status": "restored",
            "backup_id": backup_id,
            "restored_at": datetime.now(timezone.utc).isoformat(),
            "artifacts_restored": meta.get("artifacts_count", 0),
        }


backup_service = BackupRestoreService()
