import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import get_current_user_optional, get_current_user
from models.user import User
from schemas.auth import MessageResponse
from schemas.quiz import QuizCreate, QuizListResponse, QuizUpdate, QuizResponse
from services.quiz_service import (
    list_public_quizzes, create_quiz,
    get_quiz_for_view, update_quiz, delete_quiz
)

quiz_router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@quiz_router.get("", response_model=QuizListResponse)
async def get_quizzes(
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    owner_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> QuizListResponse:
    return await list_public_quizzes(db, search, category_id, owner_id, page, page_size)


@quiz_router.post("", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz_handler(
    payload: QuizCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QuizResponse:
    return await create_quiz(db, current_user, payload)


@quiz_router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz_handler(
    quiz_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional)
) -> QuizResponse:
    return await get_quiz_for_view(db, quiz_id, current_user)


@quiz_router.patch("/{quiz_id}", response_model=QuizResponse)
async def update_quiz_handler(
    quiz_id: uuid.UUID, payload: QuizUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QuizResponse:
    return await update_quiz(db, current_user, quiz_id, payload)


@quiz_router.delete("/{quiz_id}", response_model=MessageResponse)
async def delete_quiz_handler(
    quiz_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    await delete_quiz(db, current_user, quiz_id)
    return MessageResponse(message="Quiz deleted")
