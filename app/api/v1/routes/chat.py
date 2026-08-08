from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.deps import get_conversation_repository, get_current_user, get_rag_service
from app.core.cache import ResponseCache, cache_key, get_response_cache
from app.core.exceptions import ConversationNotFoundError, ForbiddenError, RateLimitExceededError
from app.core.rate_limit import RateLimiter, get_rate_limiter
from app.db.models import User
from app.db.repositories import ConversationRepository
from app.observability.metrics import CACHE_HITS, CACHE_MISSES
from app.rag.service import RAGService
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

_CACHE_TTL_SECONDS = 300


async def _ensure_conversation(
    conversation_id: str | None, user_id: str, conversation_repository: ConversationRepository
) -> str:
    if conversation_id is None:
        conversation = await conversation_repository.create(user_id)
        return conversation.id
    conversation = await conversation_repository.get_by_id(conversation_id)
    if conversation is None:
        raise ConversationNotFoundError("Conversation not found")
    if conversation.user_id != user_id:
        raise ForbiddenError("You do not have access to this conversation")
    return conversation.id


async def _check_rate_limit(user_id: str, rate_limiter: RateLimiter) -> None:
    from app.core.config import get_settings

    settings = get_settings()
    if not await rate_limiter.is_allowed(user_id, settings.rate_limit_per_minute):
        raise RateLimitExceededError("Rate limit exceeded. Please slow down.")


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    rag_service: RAGService = Depends(get_rag_service),
    cache: ResponseCache = Depends(get_response_cache),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ChatResponse:
    await _check_rate_limit(current_user.id, rate_limiter)
    conversation_id = await _ensure_conversation(
        payload.conversation_id, current_user.id, conversation_repository
    )

    key = cache_key(current_user.id, f"{conversation_id}:{payload.message}")
    cached = await cache.get(key)
    if cached is not None:
        CACHE_HITS.inc()
        return ChatResponse.model_validate(cached)
    CACHE_MISSES.inc()

    result = await rag_service.answer_question(current_user.id, conversation_id, payload.message)
    response = ChatResponse(
        answer=result["answer"],
        conversation_id=result["conversation_id"],
        citations=result["citations"],
        retrieval=result["retrieval"],
        metadata=result["metadata"],
    )
    await cache.set(key, response.model_dump(), _CACHE_TTL_SECONDS)
    return response


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    rag_service: RAGService = Depends(get_rag_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> StreamingResponse:
    await _check_rate_limit(current_user.id, rate_limiter)
    conversation_id = await _ensure_conversation(
        payload.conversation_id, current_user.id, conversation_repository
    )

    async def event_generator():
        result = await rag_service.answer_question(
            current_user.id, conversation_id, payload.message
        )
        answer = result["answer"]
        # Stream the already-generated answer in word chunks (SSE). The LLM
        # call itself is not token-streamed here to keep provider abstraction simple.
        for word in answer.split(" "):
            yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        final_payload = {
            "done": True,
            "citations": result["citations"],
            "metadata": result["metadata"],
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
