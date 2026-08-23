import pytest
from app.core.errors import BadRequestError
from app.services.file_storage_service import FileStorageService


def test_file_storage_save_and_read(tmp_path):
    storage = FileStorageService(base_dir=str(tmp_path))
    content = b"Sample candidate resume plain text."
    file_path, sha256_hash, size_bytes = storage.save_resume_file(
        filename="my_resume.txt", content_bytes=content, mime_type="text/plain"
    )

    assert file_path is not None
    assert len(sha256_hash) == 64
    assert size_bytes == len(content)

    # Read content back
    read_text = storage.read_file_text(file_path)
    assert read_text == "Sample candidate resume plain text."


def test_file_storage_path_sanitization(tmp_path):
    storage = FileStorageService(base_dir=str(tmp_path))
    content = b"Malicious traversal test"
    file_path, _, _ = storage.save_resume_file(
        filename="../../etc/passwd.txt", content_bytes=content
    )

    # Path must remain inside tmp_path / resumes
    assert ".." not in file_path
    assert "passwd.txt" in file_path


def test_file_storage_disallowed_extension(tmp_path):
    storage = FileStorageService(base_dir=str(tmp_path))
    with pytest.raises(BadRequestError) as exc_info:
        storage.save_resume_file(
            filename="malicious_script.sh", content_bytes=b"echo hack", mime_type="application/x-sh"
        )
    assert "Unsupported file extension" in str(exc_info.value)
