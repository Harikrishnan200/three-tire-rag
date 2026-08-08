from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


def test_liveness_endpoint() -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_settings_load_with_defaults() -> None:
    settings = get_settings()
    assert settings.llm_provider == "groq"
    assert settings.embedding_model
    assert settings.jwt_algorithm == "HS256"
