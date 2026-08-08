"""VectorRepository abstraction over Qdrant with strict per-user isolation."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import get_settings


@dataclass
class VectorChunk:
    text: str
    embedding: list[float]
    document_id: str
    user_id: str
    chunk_index: int
    page: int | None = None
    point_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class VectorSearchResult:
    text: str
    score: float
    document_id: str
    chunk_id: str
    page: int | None = None


class VectorRepository(ABC):
    @abstractmethod
    async def upsert_chunks(self, chunks: list[VectorChunk]) -> None: ...

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        user_id: str,
        limit: int = 5,
        document_id: str | None = None,
    ) -> list[VectorSearchResult]: ...

    @abstractmethod
    async def delete_document(self, document_id: str) -> None: ...

    @abstractmethod
    async def delete_user_documents(self, user_id: str) -> None: ...


class QdrantVectorRepository(VectorRepository):
    def __init__(self, client: QdrantClient, collection: str, vector_size: int) -> None:
        self._client = client
        self._collection = collection
        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size: int) -> None:
        collections = {c.name for c in self._client.get_collections().collections}
        if self._collection not in collections:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=qmodels.VectorParams(
                    size=vector_size, distance=qmodels.Distance.COSINE
                ),
            )

    async def upsert_chunks(self, chunks: list[VectorChunk]) -> None:
        points = [
            qmodels.PointStruct(
                id=c.point_id,
                vector=c.embedding,
                payload={
                    "text": c.text,
                    "document_id": c.document_id,
                    "user_id": c.user_id,
                    "chunk_index": c.chunk_index,
                    "page": c.page,
                },
            )
            for c in chunks
        ]
        self._client.upsert(collection_name=self._collection, points=points)

    async def search(
        self,
        query_embedding: list[float],
        user_id: str,
        limit: int = 5,
        document_id: str | None = None,
    ) -> list[VectorSearchResult]:
        must = [qmodels.FieldCondition(key="user_id", match=qmodels.MatchValue(value=user_id))]
        if document_id:
            must.append(
                qmodels.FieldCondition(
                    key="document_id", match=qmodels.MatchValue(value=document_id)
                )
            )
        hits = self._client.search(
            collection_name=self._collection,
            query_vector=query_embedding,
            query_filter=qmodels.Filter(must=must),
            limit=limit,
        )
        return [
            VectorSearchResult(
                text=h.payload.get("text", ""),
                score=h.score,
                document_id=h.payload.get("document_id", ""),
                chunk_id=str(h.id),
                page=h.payload.get("page"),
            )
            for h in hits
        ]

    async def delete_document(self, document_id: str) -> None:
        self._client.delete(
            collection_name=self._collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id", match=qmodels.MatchValue(value=document_id)
                        )
                    ]
                )
            ),
        )

    async def delete_user_documents(self, user_id: str) -> None:
        self._client.delete(
            collection_name=self._collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="user_id", match=qmodels.MatchValue(value=user_id)
                        )
                    ]
                )
            ),
        )


@lru_cache
def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url)
