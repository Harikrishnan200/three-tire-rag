from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str


class Citation(BaseModel):
    source_type: str
    document_id: str | None = None
    chunk_id: str | None = None
    page: int | None = None
    tier: int | None = None
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None


class RetrievalSummary(BaseModel):
    tier_1: list[dict[str, Any]] = []
    tier_2: list[dict[str, Any]] = []
    tier_3: list[dict[str, Any]] = []


class ChatMetadata(BaseModel):
    latency_ms: int
    model: str


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    citations: list[Citation]
    retrieval: RetrievalSummary
    metadata: ChatMetadata


class ConversationResponse(BaseModel):
    id: str
    title: str


class ConversationCreateRequest(BaseModel):
    title: str = "New conversation"
