from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/graphrag"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "document_chunks"

    # LLM (Groq)
    llm_provider: Literal["groq"] = "groq"
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_timeout_seconds: int = 30

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Auth
    jwt_secret: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # Uploads
    max_upload_size_mb: int = 20
    upload_dir: str = "/tmp/graphrag-uploads"

    # Rate limiting
    rate_limit_per_minute: int = 20

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
