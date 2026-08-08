from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, UploadFile

from app.api.v1.deps import get_current_user, get_document_repository
from app.core.config import Settings, get_settings
from app.core.exceptions import DocumentNotFoundError, ForbiddenError
from app.db.models import User
from app.db.repositories import DocumentRepository
from app.ingestion.service import content_hash
from app.ingestion.validation import validate_upload
from app.schemas.documents import DocumentResponse, DocumentStatusResponse, DocumentUploadResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    document_repository: DocumentRepository = Depends(get_document_repository),
    settings: Settings = Depends(get_settings),
) -> DocumentUploadResponse:
    content = await file.read()
    safe_name = validate_upload(
        file.filename or "upload",
        file.content_type or "application/octet-stream",
        len(content),
        settings.max_upload_size_mb,
    )

    file_hash = content_hash(content)
    existing = await document_repository.get_by_hash(current_user.id, file_hash)
    if existing is not None:
        job = await document_repository.get_latest_job_for_document(existing.id)
        return DocumentUploadResponse(
            document_id=existing.id, job_id=job.id if job else "", status=existing.status
        )

    os.makedirs(settings.upload_dir, exist_ok=True)
    storage_path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}_{safe_name}")
    with open(storage_path, "wb") as f:
        f.write(content)

    document = await document_repository.create(
        user_id=current_user.id,
        filename=safe_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        content_hash=file_hash,
        storage_path=storage_path,
    )
    job = await document_repository.create_ingestion_job(document.id)

    from app.workers.tasks import process_document_task

    process_document_task.delay(
        document.id, job.id, current_user.id, storage_path, document.content_type
    )

    return DocumentUploadResponse(document_id=document.id, job_id=job.id, status="PENDING")


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    document_repository: DocumentRepository = Depends(get_document_repository),
) -> list[DocumentResponse]:
    documents = await document_repository.list_for_user(current_user.id)
    return [DocumentResponse.model_validate(d, from_attributes=True) for d in documents]


async def _get_owned_document(
    document_id: str, current_user: User, document_repository: DocumentRepository
):
    document = await document_repository.get_by_id(document_id)
    if document is None:
        raise DocumentNotFoundError("Document not found")
    if document.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this document")
    return document


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    document_repository: DocumentRepository = Depends(get_document_repository),
) -> DocumentResponse:
    document = await _get_owned_document(document_id, current_user, document_repository)
    return DocumentResponse.model_validate(document, from_attributes=True)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    document_repository: DocumentRepository = Depends(get_document_repository),
) -> None:
    await _get_owned_document(document_id, current_user, document_repository)
    await document_repository.delete(document_id)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    document_repository: DocumentRepository = Depends(get_document_repository),
) -> DocumentStatusResponse:
    document = await _get_owned_document(document_id, current_user, document_repository)
    job = await document_repository.get_latest_job_for_document(document_id)
    return DocumentStatusResponse(
        document_id=document.id, status=document.status, error=job.error if job else None
    )
