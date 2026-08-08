from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Deterministic GraphRAG Knowledge Assistant",
    description=(
        "A production-style conversational Graph-RAG API built on a deterministic "
        "3-tier retrieval architecture (authoritative graph, historical graph, "
        "vector document search)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok"}
