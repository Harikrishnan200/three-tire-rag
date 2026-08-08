from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.models import User
from app.db.repositories import (
    ConversationRepository,
    DocumentRepository,
    MessageRepository,
    UserRepository,
)
from app.db.session import get_db
from app.embeddings.provider import EmbeddingProvider, get_embedding_provider
from app.graph.container import get_graph_repository as _get_graph_repository
from app.graph.repository import GraphRepository
from app.llm.provider import LLMProvider, get_llm_provider
from app.rag.entity_extraction import EntityExtractor, get_entity_extractor
from app.rag.service import RAGService
from app.vector.container import get_vector_repository as _get_vector_repository
from app.vector.repository import VectorRepository


async def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


async def get_conversation_repository(
    session: AsyncSession = Depends(get_db),
) -> ConversationRepository:
    return ConversationRepository(session)


async def get_message_repository(session: AsyncSession = Depends(get_db)) -> MessageRepository:
    return MessageRepository(session)


async def get_document_repository(session: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(session)


def get_graph_repository() -> GraphRepository:
    return _get_graph_repository()


def get_vector_repository() -> VectorRepository:
    return _get_vector_repository()


async def get_current_user(
    authorization: str | None = Header(default=None),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    user_id = decode_access_token(token)
    if user_id is None:
        raise UnauthorizedError("Invalid or expired token")
    user = await user_repository.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    return user


async def get_rag_service(
    graph_repository: GraphRepository = Depends(get_graph_repository),
    vector_repository: VectorRepository = Depends(get_vector_repository),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    entity_extractor: EntityExtractor = Depends(get_entity_extractor),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    message_repository: MessageRepository = Depends(get_message_repository),
    settings: Settings = Depends(get_settings),
) -> RAGService:
    return RAGService(
        graph_repository=graph_repository,
        vector_repository=vector_repository,
        embedding_provider=embedding_provider,
        llm_provider=llm_provider,
        entity_extractor=entity_extractor,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        model_name=settings.llm_model,
    )


async def _unused_generator() -> AsyncGenerator[None, None]:  # pragma: no cover
    yield None
