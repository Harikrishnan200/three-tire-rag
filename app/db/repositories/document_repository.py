from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentChunk, IngestionJob


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: str,
        filename: str,
        content_type: str,
        size_bytes: int,
        content_hash: str,
        storage_path: str,
    ) -> Document:
        document = Document(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            content_hash=content_hash,
            storage_path=storage_path,
            status="PENDING",
        )
        self._session.add(document)
        await self._session.commit()
        await self._session.refresh(document)
        return document

    async def get_by_id(self, document_id: str) -> Document | None:
        return await self._session.get(Document, document_id)

    async def get_by_hash(self, user_id: str, content_hash: str) -> Document | None:
        result = await self._session.execute(
            select(Document).where(
                Document.user_id == user_id, Document.content_hash == content_hash
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str) -> list[Document]:
        result = await self._session.execute(
            select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(self, document_id: str, status: str) -> None:
        document = await self._session.get(Document, document_id)
        if document is not None:
            document.status = status
            await self._session.commit()

    async def delete(self, document_id: str) -> None:
        document = await self._session.get(Document, document_id)
        if document is not None:
            await self._session.delete(document)
            await self._session.commit()

    async def add_chunk(
        self,
        document_id: str,
        chunk_index: int,
        text: str,
        vector_point_id: str | None,
        page: int | None = None,
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            text=text,
            vector_point_id=vector_point_id,
            page=page,
        )
        self._session.add(chunk)
        await self._session.commit()
        await self._session.refresh(chunk)
        return chunk

    async def create_ingestion_job(self, document_id: str) -> IngestionJob:
        job = IngestionJob(document_id=document_id, status="PENDING")
        self._session.add(job)
        await self._session.commit()
        await self._session.refresh(job)
        return job

    async def get_ingestion_job(self, job_id: str) -> IngestionJob | None:
        return await self._session.get(IngestionJob, job_id)

    async def get_latest_job_for_document(self, document_id: str) -> IngestionJob | None:
        result = await self._session.execute(
            select(IngestionJob)
            .where(IngestionJob.document_id == document_id)
            .order_by(IngestionJob.created_at.desc())
        )
        return result.scalars().first()

    async def update_job_status(self, job_id: str, status: str, error: str | None = None) -> None:
        job = await self._session.get(IngestionJob, job_id)
        if job is not None:
            job.status = status
            job.error = error
            await self._session.commit()
