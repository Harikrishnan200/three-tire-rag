"""Ingestion pipeline logic, invoked from the Celery worker task.

Kept storage/queue-agnostic: pure functions/services over repositories, so it
can be unit-tested without Celery/Postgres/Qdrant running.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from app.core.exceptions import IngestionError
from app.db.repositories.document_repository import DocumentRepository
from app.embeddings.provider import EmbeddingProvider
from app.graph.models import GraphFact
from app.graph.repository import GraphRepository
from app.ingestion.text_extraction import chunk_text, extract_text
from app.rag.entity_extraction import EntityExtractor
from app.vector.repository import VectorChunk, VectorRepository


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class IngestionService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        vector_repository: VectorRepository,
        graph_repository: GraphRepository,
        embedding_provider: EmbeddingProvider,
        entity_extractor: EntityExtractor,
    ) -> None:
        self._documents = document_repository
        self._vector = vector_repository
        self._graph = graph_repository
        self._embeddings = embedding_provider
        self._extractor = entity_extractor

    async def process_document(self, document_id: str, job_id: str, user_id: str, content: bytes, content_type: str) -> None:
        try:
            await self._documents.update_status(document_id, "PROCESSING")
            await self._documents.update_job_status(job_id, "PROCESSING")

            text = extract_text(content, content_type)
            chunks = chunk_text(text)
            if not chunks:
                raise IngestionError("Document contained no extractable text")

            embeddings = self._embeddings.embed_documents(chunks)
            vector_chunks = [
                VectorChunk(
                    text=chunk,
                    embedding=embedding,
                    document_id=document_id,
                    user_id=user_id,
                    chunk_index=idx,
                )
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True))
            ]
            await self._vector.upsert_chunks(vector_chunks)

            for idx, (chunk, vchunk) in enumerate(zip(chunks, vector_chunks, strict=True)):
                await self._documents.add_chunk(document_id, idx, chunk, vchunk.point_id)

            entities = self._extractor.extract_entities(text)
            relationships = self._extractor.extract_relationships(text)
            now = datetime.now(timezone.utc)
            for rel in relationships:
                await self._graph.add_fact(
                    GraphFact(
                        id="",
                        subject=rel.subject,
                        predicate=rel.predicate,
                        object=rel.object,
                        source=f"document:{document_id}",
                        priority=30,  # extracted-from-document facts rank below curated tier1/tier2
                        confidence=0.5,
                        created_at=now,
                        updated_at=now,
                    )
                )
            del entities

            await self._documents.update_status(document_id, "COMPLETED")
            await self._documents.update_job_status(job_id, "COMPLETED")
        except Exception as exc:
            await self._documents.update_status(document_id, "FAILED")
            await self._documents.update_job_status(job_id, "FAILED", error=str(exc))
            raise
