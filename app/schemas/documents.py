from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    status: str
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document_id: str
    job_id: str
    status: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
    error: str | None = None
