from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from schemas.user import UserResponse, UserUpdateRequest, ChangePasswordRequest
from schemas.auth import MessageResponse
from services.user_service import (
    update_user_profile, change_user_password
)

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user


@user_router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdateRequest, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    updated = await update_user_profile(
        db, current_user,
        email=payload.email,
        username=payload.username,
    )
    return updated


@user_router.post("/me/password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    await change_user_password(db, current_user, payload.old_password, payload.new_password)
    return MessageResponse(message="Password updated")
