import pytest

pytestmark = pytest.mark.asyncio


async def test_register_and_login(client) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={"email": "a@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    assert "access_token" in response.json()

    response = await client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password_fails(client) -> None:
    await client.post(
        "/api/v1/auth/register", json={"email": "b@example.com", "password": "password123"}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": "b@example.com", "password": "wrong"}
    )
    assert response.status_code == 400


async def test_me_requires_auth(client) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user(client) -> None:
    from tests.conftest import auth_headers, register_and_login

    token = await register_and_login(client, "c@example.com")
    response = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["email"] == "c@example.com"
