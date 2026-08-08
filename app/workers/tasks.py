"""Celery tasks. Kept thin: build dependencies then delegate to IngestionService."""

from __future__ import annotations

import asyncio

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.process_document_task", bind=True, max_retries=2)
def process_document_task(
    self, document_id: str, job_id: str, user_id: str, storage_path: str, content_type: str
) -> None:
    asyncio.run(_run(document_id, job_id, user_id, storage_path, content_type))


async def _run(
    document_id: str, job_id: str, user_id: str, storage_path: str, content_type: str
) -> None:
    from app.db.repositories.document_repository import DocumentRepository
    from app.db.session import get_sessionmaker
    from app.embeddings.provider import get_embedding_provider
    from app.graph.container import get_graph_repository
    from app.ingestion.service import IngestionService
    from app.rag.entity_extraction import get_entity_extractor
    from app.vector.container import get_vector_repository

    session_factory = get_sessionmaker()
    async with session_factory() as session:
        document_repository = DocumentRepository(session)
        with open(storage_path, "rb") as f:
            content = f.read()
        service = IngestionService(
            document_repository=document_repository,
            vector_repository=get_vector_repository(),
            graph_repository=get_graph_repository(),
            embedding_provider=get_embedding_provider(),
            entity_extractor=get_entity_extractor(),
        )
        await service.process_document(document_id, job_id, user_id, content, content_type)
