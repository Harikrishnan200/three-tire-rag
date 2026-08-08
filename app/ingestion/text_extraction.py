from __future__ import annotations

import io

from app.core.exceptions import IngestionError


def extract_text(content: bytes, content_type: str) -> str:
    if content_type == "text/plain":
        return content.decode("utf-8", errors="ignore")
    if content_type == "application/pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise IngestionError(f"Failed to extract PDF text: {exc}") from exc
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        try:
            import docx

            document = docx.Document(io.BytesIO(content))
            return "\n".join(p.text for p in document.paragraphs)
        except Exception as exc:
            raise IngestionError(f"Failed to extract DOCX text: {exc}") from exc
    raise IngestionError(f"Unsupported content type: {content_type}")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = end - overlap
    return chunks
