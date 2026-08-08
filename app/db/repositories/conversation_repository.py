from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: str, title: str = "New conversation") -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self._session.add(conversation)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        return await self._session.get(Conversation, conversation_id)

    async def list_for_user(self, user_id: str) -> list[Conversation]:
        result = await self._session.execute(
            select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())
