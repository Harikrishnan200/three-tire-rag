from __future__ import annotations

import hashlib

from app.embeddings.provider import EmbeddingProvider


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic hash-based pseudo-embeddings. No model download/network."""

    def __init__(self, dim: int = 16) -> None:
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in digest[: self._dim]]

    def embed_text(self, text: str) -> list[float]:
        return self._vector(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]
