from __future__ import annotations

from typing import Any

from app.llm.provider import LLMProvider


class FakeLLMProvider(LLMProvider):
    """Deterministic stand-in for Groq. Never calls the network."""

    def __init__(self, canned_answer: str = "This is a test answer based on the supplied evidence.") -> None:
        self.canned_answer = canned_answer
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.canned_answer

    async def generate_structured(self, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def health_check(self) -> bool:
        return True
