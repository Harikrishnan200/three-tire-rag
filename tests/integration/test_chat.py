from datetime import datetime

import pytest

from app.graph.models import GraphFact
from tests.conftest import auth_headers, register_and_login

pytestmark = pytest.mark.asyncio


async def _seed_microsoft_ceo_facts(graph_repository) -> None:
    await graph_repository.add_fact(
        GraphFact(id="1", subject="Microsoft", predicate="ceo", object="Satya Nadella", priority=100, source="curated")
    )
    await graph_repository.add_fact(
        GraphFact(
            id="2",
            subject="Microsoft",
            predicate="ceo",
            object="Steve Ballmer",
            priority=50,
            source="curated",
            valid_from=datetime(2000, 1, 13),
            valid_to=datetime(2014, 2, 4),
        )
    )


async def test_chat_creates_conversation_and_returns_answer(client, graph_repository, llm_provider) -> None:
    await _seed_microsoft_ceo_facts(graph_repository)
    token = await register_and_login(client, "chatuser@example.com")

    response = await client.post(
        "/api/v1/chat", headers=auth_headers(token), json={"conversation_id": None, "message": "Who is Microsoft's current CEO?"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == llm_provider.canned_answer
    assert body["conversation_id"]
    assert body["metadata"]["model"]
    tier1 = body["retrieval"]["tier_1"]
    assert any(f["object"] == "Satya Nadella" for f in tier1)


async def test_chat_produces_citations(client, graph_repository) -> None:
    await _seed_microsoft_ceo_facts(graph_repository)
    token = await register_and_login(client, "citeuser@example.com")
    response = await client.post(
        "/api/v1/chat", headers=auth_headers(token), json={"conversation_id": None, "message": "Who is Microsoft's current CEO?"}
    )
    citations = response.json()["citations"]
    assert any(c["source_type"] == "graph" and c["object"] == "Satya Nadella" for c in citations)


async def test_chat_rejects_access_to_other_users_conversation(client, graph_repository) -> None:
    token_a = await register_and_login(client, "convowner@example.com")
    response = await client.post(
        "/api/v1/chat", headers=auth_headers(token_a), json={"conversation_id": None, "message": "hello"}
    )
    conversation_id = response.json()["conversation_id"]

    token_b = await register_and_login(client, "intruder@example.com")
    response = await client.post(
        "/api/v1/chat", headers=auth_headers(token_b), json={"conversation_id": conversation_id, "message": "hello"}
    )
    assert response.status_code == 403


async def test_chat_response_is_cached(client, graph_repository) -> None:
    await _seed_microsoft_ceo_facts(graph_repository)
    token = await register_and_login(client, "cacheuser@example.com")
    r1 = await client.post(
        "/api/v1/chat", headers=auth_headers(token), json={"conversation_id": None, "message": "Who is Microsoft's CEO?"}
    )
    conversation_id = r1.json()["conversation_id"]
    r2 = await client.post(
        "/api/v1/chat",
        headers=auth_headers(token),
        json={"conversation_id": conversation_id, "message": "Who is Microsoft's CEO?"},
    )
    assert r2.status_code == 200


async def test_chat_rate_limiting(client, graph_repository) -> None:
    token = await register_and_login(client, "ratelimited@example.com")
    last_status = 200
    for i in range(25):
        response = await client.post(
            "/api/v1/chat",
            headers=auth_headers(token),
            json={"conversation_id": None, "message": f"question number {i}"},
        )
        last_status = response.status_code
        if last_status == 429:
            break
    assert last_status == 429
