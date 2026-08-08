import pytest

from app.core.exceptions import ValidationAppError
from app.ingestion.validation import sanitize_filename, validate_upload


def test_sanitize_filename_strips_path_traversal() -> None:
    assert sanitize_filename("../../etc/passwd") == "passwd"


def test_validate_upload_rejects_bad_content_type() -> None:
    with pytest.raises(ValidationAppError):
        validate_upload("file.exe", "application/x-msdownload", 100, 20)


def test_validate_upload_rejects_oversized_file() -> None:
    with pytest.raises(ValidationAppError):
        validate_upload("file.txt", "text/plain", 30 * 1024 * 1024, 20)


def test_validate_upload_accepts_valid_txt() -> None:
    name = validate_upload("my report.txt", "text/plain", 100, 20)
    assert name == "my_report.txt"
