import hashlib
import os
from pathlib import Path
import re
from typing import Tuple

from app.core.config import get_settings
from app.core.errors import BadRequestError
from app.core.logging import get_logger

logger = get_logger("app.services.storage")
settings = get_settings()

ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".pdf", ".docx", ".doc"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


class FileStorageService:
    """Secure Local File Storage Subsystem (100% Local, Git-Excluded)."""

    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = Path(base_dir).resolve()
        self.resumes_dir = self.base_dir / "resumes"
        self.resumes_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal and special character exploits."""
        # Strip path components
        base = os.path.basename(filename)
        # Keep only alphanumeric, dots, underscores, hyphens
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
        return sanitized or "unnamed_file.txt"

    def compute_sha256(self, content_bytes: bytes) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content_bytes).hexdigest()

    def save_resume_file(
        self, filename: str, content_bytes: bytes, mime_type: str = "text/plain"
    ) -> Tuple[str, str, int]:
        """Save a resume file securely to local storage.
        
        Returns:
            Tuple of (relative_file_path, sha256_hash, file_size_bytes)
        """
        if len(content_bytes) > MAX_FILE_SIZE_BYTES:
            raise BadRequestError(
                f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
            )

        sanitized_name = self._sanitize_filename(filename)
        ext = os.path.splitext(sanitized_name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise BadRequestError(
                f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        sha256_hash = self.compute_sha256(content_bytes)
        # Deterministic, unique on-disk filename preventing collisions
        disk_filename = f"{sha256_hash[:12]}_{sanitized_name}"
        destination_path = (self.resumes_dir / disk_filename).resolve()

        # Security check: Ensure destination is strictly inside self.resumes_dir
        if not str(destination_path).startswith(str(self.resumes_dir)):
            raise BadRequestError("Security violation: Invalid storage target path.")

        # Write file to disk
        destination_path.write_bytes(content_bytes)
        
        # Log metadata only (never log file contents)
        logger.info(
            "Saved resume file to local storage (filename=%s, hash=%s, size=%d bytes)",
            sanitized_name,
            sha256_hash[:12],
            len(content_bytes),
        )

        relative_path = str(destination_path.relative_to(Path.cwd())) if destination_path.is_relative_to(Path.cwd()) else str(destination_path)
        return relative_path, sha256_hash, len(content_bytes)

    def read_file_text(self, file_path_str: str) -> str:
        """Read text content from a stored file safely with format-aware binary handling."""
        target_path = Path(file_path_str).resolve()
        if not target_path.exists():
            raise BadRequestError("The requested stored file does not exist on disk.")

        ext = target_path.suffix.lower()
        content_bytes = target_path.read_bytes()

        if ext in [".docx", ".doc"] or content_bytes.startswith(b"PK\x03\x04"):
            from app.services.resume_parser_service import resume_parser
            return resume_parser.extract_text_from_docx(content_bytes)

        if ext == ".pdf" or content_bytes.startswith(b"%PDF"):
            from app.services.resume_parser_service import resume_parser
            return resume_parser.extract_text_from_pdf(content_bytes)

        try:
            return content_bytes.decode("utf-8", errors="replace")
        except Exception as exc:
            logger.error("Failed to read file text: %s", exc)
            raise BadRequestError(f"Could not read text from stored file: {exc}")


storage_service = FileStorageService()
