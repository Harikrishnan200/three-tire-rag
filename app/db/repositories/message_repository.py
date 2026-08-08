from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Citation, Message, RetrievalEvent


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        latency_ms: int | None = None,
        model: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            latency_ms=latency_ms,
            model=model,
        )
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def list_for_conversation(self, conversation_id: str) -> list[Message]:
        result = await self._session.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

    async def add_retrieval_event(
        self,
        message_id: str,
        tier_1: list[dict],
        tier_2: list[dict],
        tier_3: list[dict],
        conflicts: list[dict],
    ) -> RetrievalEvent:
        event = RetrievalEvent(
            message_id=message_id, tier_1=tier_1, tier_2=tier_2, tier_3=tier_3, conflicts=conflicts
        )
        self._session.add(event)
        await self._session.commit()
        return event

    async def add_citations(self, message_id: str, citations: list[dict]) -> list[Citation]:
        rows = [Citation(message_id=message_id, **c) for c in citations]
        self._session.add_all(rows)
        await self._session.commit()
        return rows
