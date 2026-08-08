import pytest

from tests.fakes.fake_vector_repository import FakeVectorRepository
from app.vector.repository import VectorChunk

pytestmark = pytest.mark.asyncio


async def test_vector_search_never_crosses_users() -> None:
    repo = FakeVectorRepository()
    await repo.upsert_chunks(
        [
            VectorChunk(text="user A secret", embedding=[1.0, 0.0], document_id="d1", user_id="user-a", chunk_index=0),
            VectorChunk(text="user B secret", embedding=[1.0, 0.0], document_id="d2", user_id="user-b", chunk_index=0),
        ]
    )
    results_a = await repo.search([1.0, 0.0], user_id="user-a")
    assert all(r.document_id == "d1" for r in results_a)
    assert len(results_a) == 1

    results_b = await repo.search([1.0, 0.0], user_id="user-b")
    assert all(r.document_id == "d2" for r in results_b)
