from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness() -> dict[str, object]:
    settings = get_settings()
    checks: dict[str, bool] = {}

    try:
        from app.db.session import get_engine

        engine = get_engine()
        async with engine.connect() as conn:
            await conn.run_sync(lambda c: None)
        checks["postgres"] = True
    except Exception:
        checks["postgres"] = False

    try:
        import redis.asyncio as redis

        client = redis.from_url(settings.redis_url)
        await client.ping()
        checks["redis"] = True
    except Exception:
        checks["redis"] = False

    try:
        from app.vector.repository import get_qdrant_client

        get_qdrant_client().get_collections()
        checks["qdrant"] = True
    except Exception:
        checks["qdrant"] = False

    checks["groq_configured"] = bool(settings.groq_api_key)

    status = "ok" if all([checks["postgres"], checks["redis"], checks["qdrant"]]) else "degraded"
    return {"status": status, "checks": checks}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
