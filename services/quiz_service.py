import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.category import Category
from models.quiz import Quiz
from models.user import User
from schemas.quiz import QuizCreate, QuizUpdate


async def list_public_quizzes(db: AsyncSession) -> list[Quiz]:
    result = await db.execute(select(Quiz).where(Quiz.is_public == True))
    return list(result.scalars().all())


async def get_quiz_by_id(db: AsyncSession, quiz_id: uuid.UUID) -> Quiz:
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    return quiz


async def get_quiz_for_view(db: AsyncSession, quiz_id: uuid.UUID, user: User | None) -> Quiz:
    quiz = await get_quiz_by_id(db, quiz_id)
    if quiz.is_public:
        return quiz

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")

    if quiz.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return quiz


async def create_quiz(db: AsyncSession, user: User, payload: QuizCreate) -> Quiz:
    if payload.category_id:
        result = await db.execute(select(Category).where(Category.id == payload.category_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")

    quiz = Quiz(
        owner_id=user.id,
        category_id=payload.category_id,
        title=payload.title,
        description=payload.description,
        time_per_question=payload.time_per_question,
        is_public=payload.is_public,
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    
    return quiz


async def update_quiz(db: AsyncSession, user: User, quiz_id: uuid.UUID, payload: QuizUpdate) -> Quiz:
    quiz = await get_quiz_by_id(db, quiz_id)
    if quiz.owner_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    if payload.category_id is not None:
        if payload.category_id:
            result = await db.execute(select(Category).where(Category.id == payload.category_id))
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found"
                )
        quiz.category_id = payload.category_id

    if payload.title is not None:
        quiz.title = payload.title
    if payload.description is not None:
        quiz.description = payload.description
    if payload.time_per_question is not None:
        quiz.time_per_question = payload.time_per_question
    if payload.is_public is not None:
        quiz.is_public = payload.is_public

    await db.commit()
    await db.refresh(quiz)

    return quiz


async def delete_quiz(db: AsyncSession, user: User, quiz_id: uuid.UUID) -> None:
    quiz = await get_quiz_by_id(db, quiz_id)
    if quiz.owner_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    await db.delete(quiz)
    await db.commit()
