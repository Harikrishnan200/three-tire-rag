from __future__ import annotations

import os
import re

from app.core.exceptions import ValidationAppError

ALLOWED_CONTENT_TYPES = {
    "text/plain": ".txt",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    base = os.path.basename(filename)
    base = _SAFE_FILENAME_RE.sub("_", base)
    if not base or base in (".", ".."):
        raise ValidationAppError("Invalid filename")
    return base


def validate_upload(filename: str, content_type: str, size_bytes: int, max_size_mb: int) -> str:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationAppError(f"Unsupported file type: {content_type}. Allowed: PDF, TXT, DOCX.")
    max_bytes = max_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValidationAppError(f"File too large: {size_bytes} bytes exceeds {max_size_mb}MB limit.")
    return sanitize_filename(filename)
