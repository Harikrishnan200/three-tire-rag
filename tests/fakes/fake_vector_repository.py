from __future__ import annotations

from app.vector.repository import VectorChunk, VectorRepository, VectorSearchResult


class FakeVectorRepository(VectorRepository):
    """In-memory vector store with strict user_id isolation, for tests."""

    def __init__(self) -> None:
        self._chunks: list[VectorChunk] = []

    async def upsert_chunks(self, chunks: list[VectorChunk]) -> None:
        self._chunks.extend(chunks)

    async def search(
        self,
        query_embedding: list[float],
        user_id: str,
        limit: int = 5,
        document_id: str | None = None,
    ) -> list[VectorSearchResult]:
        candidates = [c for c in self._chunks if c.user_id == user_id]
        if document_id:
            candidates = [c for c in candidates if c.document_id == document_id]

        def score(chunk: VectorChunk) -> float:
            # simple cosine-ish similarity for deterministic ranking in tests
            a, b = chunk.embedding, query_embedding
            n = min(len(a), len(b))
            return sum(a[i] * b[i] for i in range(n))

        ranked = sorted(candidates, key=score, reverse=True)[:limit]
        return [
            VectorSearchResult(
                text=c.text,
                score=score(c),
                document_id=c.document_id,
                chunk_id=c.point_id,
                page=c.page,
            )
            for c in ranked
        ]

    async def delete_document(self, document_id: str) -> None:
        self._chunks = [c for c in self._chunks if c.document_id != document_id]

    async def delete_user_documents(self, user_id: str) -> None:
        self._chunks = [c for c in self._chunks if c.user_id != user_id]
