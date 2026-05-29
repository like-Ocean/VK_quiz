import uuid
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from schemas.auth import MessageResponse
from schemas.question import (
    QuestionCreate, QuestionUpdate,
    QuestionResponse, QuestionReorderRequest,
)
from schemas.room import ImageUploadResponse
from services import question_service
import os
import uuid as uuid_lib

question_router = APIRouter(tags=["questions"])


@question_router.post(
    "/quizzes/{quiz_id}/questions", 
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_question(
    quiz_id: uuid.UUID, payload: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QuestionResponse:
    return await question_service.create_question(db, current_user, quiz_id, payload)


@question_router.get("/quizzes/{quiz_id}/questions", response_model=list[QuestionResponse])
async def get_questions_handler(
    quiz_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[QuestionResponse]:
    return await question_service.get_questions(db, quiz_id)


@question_router.patch("/quizzes/{quiz_id}/questions/{question_id}", response_model=QuestionResponse)
async def update_question_handler(
    quiz_id: uuid.UUID, question_id: uuid.UUID,
    payload: QuestionUpdate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionResponse:
    return await question_service.update_question(db, current_user, quiz_id, question_id, payload)


@question_router.delete("/quizzes/{quiz_id}/questions/{question_id}", response_model=MessageResponse)
async def delete_question_handler(
    quiz_id: uuid.UUID, question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    await question_service.delete_question(db, current_user, quiz_id, question_id)

    return MessageResponse(message="Question deleted")


@question_router.patch("/quizzes/{quiz_id}/questions/reorder", response_model=MessageResponse)
async def reorder_questions_handler(
    quiz_id: uuid.UUID, payload: QuestionReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    await question_service.reorder_questions(db, current_user, quiz_id, payload.question_ids)
    
    return MessageResponse(message="Questions reordered")


@question_router.post("/uploads/image", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)) -> ImageUploadResponse:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    extension = os.path.splitext(file.filename or "")[1]
    filename = f"{uuid_lib.uuid4().hex}{extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return ImageUploadResponse(image_url=f"/uploads/{filename}")
