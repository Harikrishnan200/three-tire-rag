"""Centralized custom exceptions mapped to consistent JSON error responses."""

from __future__ import annotations


class AppError(Exception):
    """Base application error. code is a stable machine-readable identifier."""

    code: str = "internal_error"
    status_code: int = 500

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class DocumentNotFoundError(AppError):
    code = "document_not_found"
    status_code = 404


class ConversationNotFoundError(AppError):
    code = "conversation_not_found"
    status_code = 404


class UnauthorizedError(AppError):
    code = "unauthorized"
    status_code = 401


class ForbiddenError(AppError):
    code = "forbidden"
    status_code = 403


class IngestionError(AppError):
    code = "ingestion_error"
    status_code = 422


class RetrievalError(AppError):
    code = "retrieval_error"
    status_code = 502


class LLMError(AppError):
    code = "llm_error"
    status_code = 502


class VectorStoreError(AppError):
    code = "vector_store_error"
    status_code = 502


class GraphStoreError(AppError):
    code = "graph_store_error"
    status_code = 502


class RateLimitExceededError(AppError):
    code = "rate_limit_exceeded"
    status_code = 429


class ValidationAppError(AppError):
    code = "validation_error"
    status_code = 400


class ConflictError(AppError):
    code = "conflict"
    status_code = 409
