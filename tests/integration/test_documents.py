import pytest

from tests.conftest import auth_headers, register_and_login

pytestmark = pytest.mark.asyncio


async def test_upload_requires_auth(client) -> None:
    response = await client.post("/api/v1/documents/upload", files={"file": ("a.txt", b"hello", "text/plain")})
    assert response.status_code == 401


async def test_upload_document_and_ownership(client, monkeypatch) -> None:
    # Avoid touching Celery broker in tests: patch the task's .delay to a no-op.
    from app.workers import tasks

    monkeypatch.setattr(tasks.process_document_task, "delay", lambda *a, **k: None)

    token_a = await register_and_login(client, "owner@example.com")
    response = await client.post(
        "/api/v1/documents/upload",
        headers=auth_headers(token_a),
        files={"file": ("notes.txt", b"Microsoft was founded in 1975.", "text/plain")},
    )
    assert response.status_code == 202
    document_id = response.json()["document_id"]

    # Owner can access.
    response = await client.get(f"/api/v1/documents/{document_id}", headers=auth_headers(token_a))
    assert response.status_code == 200

    # Another user cannot access.
    token_b = await register_and_login(client, "other@example.com")
    response = await client.get(f"/api/v1/documents/{document_id}", headers=auth_headers(token_b))
    assert response.status_code == 403


async def test_upload_rejects_bad_file_type(client, monkeypatch) -> None:
    from app.workers import tasks

    monkeypatch.setattr(tasks.process_document_task, "delay", lambda *a, **k: None)

    token = await register_and_login(client, "badfile@example.com")
    response = await client.post(
        "/api/v1/documents/upload",
        headers=auth_headers(token),
        files={"file": ("virus.exe", b"MZ", "application/x-msdownload")},
    )
    assert response.status_code == 400
