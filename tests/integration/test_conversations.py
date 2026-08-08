import pytest

from tests.conftest import auth_headers, register_and_login

pytestmark = pytest.mark.asyncio


async def test_create_and_list_conversations(client) -> None:
    token = await register_and_login(client, "convuser@example.com")
    response = await client.post(
        "/api/v1/conversations", headers=auth_headers(token), json={"title": "Test chat"}
    )
    assert response.status_code == 201
    conversation_id = response.json()["id"]

    response = await client.get("/api/v1/conversations", headers=auth_headers(token))
    assert response.status_code == 200
    ids = [c["id"] for c in response.json()]
    assert conversation_id in ids
