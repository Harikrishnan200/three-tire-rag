from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user, get_user_repository
from app.core.exceptions import ValidationAppError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.repositories import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    payload: RegisterRequest, user_repository: UserRepository = Depends(get_user_repository)
) -> TokenResponse:
    existing = await user_repository.get_by_email(payload.email)
    if existing is not None:
        raise ValidationAppError("Email already registered")
    user = await user_repository.create(payload.email, hash_password(payload.password))
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, user_repository: UserRepository = Depends(get_user_repository)
) -> TokenResponse:
    user = await user_repository.get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise ValidationAppError("Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=current_user.id, email=current_user.email)
