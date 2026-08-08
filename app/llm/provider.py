"""LLMProvider abstraction. Never hardcode model names outside config."""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import LLMError


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str: ...

    @abstractmethod
    async def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def health_check(self) -> bool: ...


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    def _client(self) -> Any:
        from groq import AsyncGroq

        return AsyncGroq(api_key=self._api_key, timeout=self._timeout_seconds)

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        try:
            client = self._client()
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            content = response.choices[0].message.content
            return content or ""
        except Exception as exc:  # pragma: no cover - network failure path
            raise LLMError(f"Groq generation failed: {exc}") from exc

    async def generate_structured(
        self, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        import json

        try:
            client = self._client()
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            content = response.choices[0].message.content or "{}"
            result: dict[str, Any] = json.loads(content)
            return result
        except Exception as exc:  # pragma: no cover - network failure path
            raise LLMError(f"Groq structured generation failed: {exc}") from exc

    async def health_check(self) -> bool:
        return bool(self._api_key)


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    return GroqProvider(
        api_key=settings.groq_api_key, model=settings.llm_model, timeout_seconds=settings.llm_timeout_seconds
    )
