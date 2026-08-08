import pytest

from app.core.exceptions import IngestionError
from app.db.repositories.document_repository import DocumentRepository
from app.graph.repository import NetworkXGraphRepository
from app.ingestion.service import IngestionService
from tests.fakes.fake_embeddings import FakeEmbeddingProvider
from tests.fakes.fake_entity_extractor import FakeEntityExtractor
from tests.fakes.fake_vector_repository import FakeVectorRepository

pytestmark = pytest.mark.asyncio


async def test_ingestion_marks_document_failed_on_unsupported_content(db_session) -> None:
    document_repository = DocumentRepository(db_session)
    document = await document_repository.create(
        user_id="u1",
        filename="bad.bin",
        content_type="application/octet-stream",
        size_bytes=3,
        content_hash="abc",
        storage_path="/tmp/bad.bin",
    )
    job = await document_repository.create_ingestion_job(document.id)

    service = IngestionService(
        document_repository=document_repository,
        vector_repository=FakeVectorRepository(),
        graph_repository=NetworkXGraphRepository(),
        embedding_provider=FakeEmbeddingProvider(),
        entity_extractor=FakeEntityExtractor(),
    )

    with pytest.raises(IngestionError):
        await service.process_document(
            document.id, job.id, "u1", b"junk", "application/octet-stream"
        )

    refreshed = await document_repository.get_by_id(document.id)
    refreshed_job = await document_repository.get_ingestion_job(job.id)
    assert refreshed.status == "FAILED"
    assert refreshed_job.status == "FAILED"
    assert refreshed_job.error
