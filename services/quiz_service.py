import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.category import Category
from models.question import Question
from models.quiz import Quiz
from models.room import Room, RoomStatus
from models.room_participant import RoomParticipant
from models.user import User
from schemas.quiz import QuizCreate, QuizUpdate, QuizListResponse


async def list_public_quizzes(
    db: AsyncSession, search: str | None = None,
    category_id: uuid.UUID | None = None,
    owner_id: uuid.UUID | None = None,
    page: int = 1, page_size: int = 10,
) -> QuizListResponse:
    query = (
        select(Quiz)
        .where(Quiz.is_public == True)
        .options(selectinload(Quiz.category))
    )

    if search:
        query = query.where(Quiz.title.ilike(f"%{search}%"))
    if category_id:
        query = query.where(Quiz.category_id == category_id)
    if owner_id:
        query = query.where(Quiz.owner_id == owner_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    quizzes = list(result.scalars().all())

    items: list[dict] = []
    for quiz in quizzes:
        q_count_result = await db.execute(
            select(func.count(Question.id)).where(Question.quiz_id == quiz.id)
        )
        questions_count = q_count_result.scalar_one() or 0
        room_result = await db.execute(
            select(Room).where(
                Room.quiz_id == quiz.id,
                Room.status != RoomStatus.finished,
            )
        )
        room = room_result.scalar_one_or_none()

        participants_count: int | None = None
        room_status: RoomStatus | None = None
        if room:
            room_status = room.status
            p_result = await db.execute(
                select(func.count(RoomParticipant.id)).where(
                    RoomParticipant.room_id == room.id
                )
            )
            participants_count = p_result.scalar_one() or 0

        items.append(
            {
                "id": quiz.id,
                "owner_id": quiz.owner_id,
                "category_id": quiz.category_id,
                "category_name": quiz.category.name if quiz.category else None,
                "title": quiz.title,
                "description": quiz.description,
                "time_per_question": quiz.time_per_question,
                "is_public": quiz.is_public,
                "created_at": quiz.created_at,
                "updated_at": quiz.updated_at,
                "questions_count": questions_count,
                "participants_count": participants_count,
                "room_status": room_status,
            }
        )

    return QuizListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, -(-total // page_size)),
    )


async def get_quiz_by_id(db: AsyncSession, quiz_id: uuid.UUID) -> Quiz:
    result = await db.execute(
        select(Quiz)
        .where(Quiz.id == quiz_id)
        .options(selectinload(Quiz.category))
    )
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

    return await get_quiz_by_id(db, quiz.id)


async def update_quiz(db: AsyncSession, user: User, quiz_id: uuid.UUID, payload: QuizUpdate) -> Quiz:
    quiz = await get_quiz_by_id(db, quiz_id)
    if quiz.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if payload.category_id is not None:
        if payload.category_id:
            result = await db.execute(select(Category).where(Category.id == payload.category_id))
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")
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

    return await get_quiz_by_id(db, quiz_id)


async def delete_quiz(db: AsyncSession, user: User, quiz_id: uuid.UUID) -> None:
    quiz = await get_quiz_by_id(db, quiz_id)
    if quiz.owner_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    await db.delete(quiz)
    await db.commit()
