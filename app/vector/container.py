from functools import lru_cache

from app.core.config import get_settings
from app.vector.repository import QdrantVectorRepository, VectorRepository, get_qdrant_client


@lru_cache
def get_vector_repository() -> VectorRepository:
    settings = get_settings()
    from app.embeddings.provider import get_embedding_provider

    dimension = get_embedding_provider().dimension
    return QdrantVectorRepository(get_qdrant_client(), settings.qdrant_collection, dimension)
