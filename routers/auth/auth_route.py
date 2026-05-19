from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from schemas.auth import (
    RegisterRequest, LoginRequest,
    TokenResponse, RefreshTokenRequest,
    MessageResponse,
)
from services.auth_service import (
    authenticate_user, register_user,
    issue_tokens, refresh_tokens, logout_user
)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await register_user(
        db, email=payload.email,
        username=payload.username,
        password=payload.password
    )

    access_token, refresh_token = await issue_tokens(db, user.id)
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@auth_router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await authenticate_user(db, payload.email, payload.password)

    access_token, refresh_token = await issue_tokens(db, user.id)
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    access_token, refresh_token = await refresh_tokens(db, payload.refresh_token)
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@auth_router.post("/logout", response_model=MessageResponse)
async def logout(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await logout_user(db, payload.refresh_token)
    
    return MessageResponse(message="Logged out")
