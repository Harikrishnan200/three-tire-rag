from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.deps import (
    get_current_user,
    get_graph_repository,
    get_rag_service,
    get_vector_repository,
)
from app.core.cache import InMemoryResponseCache, get_response_cache
from app.core.rate_limit import InMemoryRateLimiter, get_rate_limiter
from app.db.base import Base
from app.db.models import models  # noqa: F401 ensures models registered
from app.db.session import get_db
from app.embeddings.provider import get_embedding_provider
from app.graph.repository import GraphRepository, NetworkXGraphRepository
from app.llm.provider import get_llm_provider
from app.main import app
from app.rag.entity_extraction import get_entity_extractor
from app.rag.service import RAGService
from app.vector.repository import VectorRepository
from tests.fakes.fake_embeddings import FakeEmbeddingProvider
from tests.fakes.fake_entity_extractor import FakeEntityExtractor
from tests.fakes.fake_llm import FakeLLMProvider
from tests.fakes.fake_vector_repository import FakeVectorRepository


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
def graph_repository() -> GraphRepository:
    return NetworkXGraphRepository()


@pytest.fixture
def vector_repository() -> VectorRepository:
    return FakeVectorRepository()


@pytest.fixture
def llm_provider() -> FakeLLMProvider:
    return FakeLLMProvider()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    graph_repository: GraphRepository,
    vector_repository: VectorRepository,
    llm_provider: FakeLLMProvider,
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    fake_cache = InMemoryResponseCache()
    fake_rate_limiter = InMemoryRateLimiter()
    fake_embeddings = FakeEmbeddingProvider()
    fake_extractor = FakeEntityExtractor()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_graph_repository] = lambda: graph_repository
    app.dependency_overrides[get_vector_repository] = lambda: vector_repository
    app.dependency_overrides[get_embedding_provider] = lambda: fake_embeddings
    app.dependency_overrides[get_llm_provider] = lambda: llm_provider
    app.dependency_overrides[get_entity_extractor] = lambda: fake_extractor
    app.dependency_overrides[get_response_cache] = lambda: fake_cache
    app.dependency_overrides[get_rate_limiter] = lambda: fake_rate_limiter

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def register_and_login(client: AsyncClient, email: str, password: str = "testpassword123") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return token


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
