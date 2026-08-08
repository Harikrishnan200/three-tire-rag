from fastapi import APIRouter, Depends

from app.api.v1.deps import get_conversation_repository, get_current_user
from app.db.models import User
from app.db.repositories import ConversationRepository
from app.schemas.chat import ConversationCreateRequest, ConversationResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    payload: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
) -> ConversationResponse:
    conversation = await conversation_repository.create(current_user.id, payload.title)
    return ConversationResponse(id=conversation.id, title=conversation.title)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
) -> list[ConversationResponse]:
    conversations = await conversation_repository.list_for_user(current_user.id)
    return [ConversationResponse(id=c.id, title=c.title) for c in conversations]
