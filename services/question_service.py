import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.answer_option import AnswerOption
from models.question import Question
from models.user import User
from schemas.question import QuestionCreate, QuestionUpdate
from helpers.quiz import _get_quiz_for_edit


async def create_question(
    db: AsyncSession, user: User, quiz_id: uuid.UUID, payload: QuestionCreate
) -> Question:
    await _get_quiz_for_edit(db, user, quiz_id)

    question = Question(
        quiz_id=quiz_id,
        order=payload.order,
        text=payload.text,
        image_url=payload.image_url,
        question_type=payload.question_type,
        answer_type=payload.answer_type,
        points=payload.points,
    )
    db.add(question)
    await db.flush()

    for option in payload.answer_options:
        db.add(AnswerOption(
            question_id=question.id,
            text=option.text,
            is_correct=option.is_correct,
        ))

    await db.commit()

    result = await db.execute(
        select(Question)
        .where(Question.id == question.id)
        .options(selectinload(Question.answer_options))
    )
    return result.scalar_one()


async def get_questions(db: AsyncSession, quiz_id: uuid.UUID) -> list[Question]:
    result = await db.execute(
        select(Question)
        .where(Question.quiz_id == quiz_id)
        .options(selectinload(Question.answer_options))
        .order_by(Question.order)
    )
    return list(result.scalars().all())


async def update_question(
    db: AsyncSession, user: User, quiz_id: uuid.UUID,
    question_id: uuid.UUID, payload: QuestionUpdate
) -> Question:
    await _get_quiz_for_edit(db, user, quiz_id)

    result = await db.execute(
        select(Question).where(Question.id == question_id, Question.quiz_id == quiz_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )

    if payload.order is not None:
        question.order = payload.order
    if payload.text is not None:
        question.text = payload.text
    if payload.image_url is not None:
        question.image_url = payload.image_url
    if payload.question_type is not None:
        question.question_type = payload.question_type
    if payload.answer_type is not None:
        question.answer_type = payload.answer_type
    if payload.points is not None:
        question.points = payload.points

    if payload.answer_options is not None:
        await db.execute(
            AnswerOption.__table__.delete().where(AnswerOption.question_id == question.id)
        )
        for option in payload.answer_options:
            if option.text is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Answer option text is required",
                )
            db.add(
                AnswerOption(
                    question_id=question.id,
                    text=option.text,
                    is_correct=option.is_correct or False,
                )
            )

    await db.commit()

    result = await db.execute(
        select(Question)
        .where(Question.id == question.id)
        .options(selectinload(Question.answer_options))
    )
    return result.scalar_one()


async def delete_question(db: AsyncSession, user: User, quiz_id: uuid.UUID, question_id: uuid.UUID):
    await _get_quiz_for_edit(db, user, quiz_id)
    result = await db.execute(
        select(Question).where(Question.id == question_id, Question.quiz_id == quiz_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    await db.delete(question)
    await db.flush()

    await db.commit()


async def reorder_questions(db: AsyncSession, user: User, quiz_id: uuid.UUID, question_ids: list[uuid.UUID]):
    await _get_quiz_for_edit(db, user, quiz_id)

    result = await db.execute(select(Question).where(Question.quiz_id == quiz_id))
    questions = list(result.scalars().all())
    existing_ids = {q.id for q in questions}

    if set(question_ids) != existing_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question list mismatch")

    order_map = {qid: idx for idx, qid in enumerate(question_ids)}
    for question in questions:
        question.order = order_map[question.id]

    await db.commit()
