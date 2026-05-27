import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from core.database import AsyncSessionLocal
from models.question import Question
from models.quiz import Quiz
from models.room import Room
from models.room_participant import RoomParticipant
from models.user import User
from services.room_manager import room_manager


async def load_participant(
    db: AsyncSession,
    room_id: uuid.UUID,
    subject_id: uuid.UUID,
) -> tuple[RoomParticipant | None, User | None]:
    user_result = await db.execute(select(User).where(User.id == subject_id))
    user = user_result.scalar_one_or_none()

    if user:
        participant_result = await db.execute(
            select(RoomParticipant).where(
                RoomParticipant.room_id == room_id,
                RoomParticipant.user_id == user.id,
            )
        )
        participant = participant_result.scalar_one_or_none()
        return participant, user

    participant_result = await db.execute(
        select(RoomParticipant).where(
            RoomParticipant.id == subject_id,
            RoomParticipant.room_id == room_id,
        )
    )
    participant = participant_result.scalar_one_or_none()
    return participant, None


async def get_owner_participant_id(db: AsyncSession, room: Room) -> str | None:
    result = await db.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room.id,
            RoomParticipant.user_id == room.owner_id,
        )
    )
    participant = result.scalar_one_or_none()
    return str(participant.id) if participant else None


async def get_quiz(db: AsyncSession, quiz_id: uuid.UUID) -> Quiz:
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    return result.scalar_one()


async def question_payload(
    db: AsyncSession, question: Question, index: int, total: int, time_limit: int
) -> dict:
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.answer_options))
        .where(Question.id == question.id)
    )
    question = result.scalar_one()
    options = [{"id": str(opt.id), "text": opt.text} for opt in question.answer_options]

    return {
        "event": "question_start",
        "question_id": str(question.id),
        "text": question.text,
        "image_url": question.image_url,
        "answer_type": question.answer_type,
        "options": options,
        "time_limit": time_limit,
        "index": index,
        "total": total,
    }


async def question_end_payload(db: AsyncSession, room: Room, question: Question) -> dict:
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.answer_options))
        .where(Question.id == question.id)
    )
    question = result.scalar_one()
    correct_ids = [str(opt.id) for opt in question.answer_options if opt.is_correct]

    leaderboard = await get_leaderboard(db, room)

    return {
        "event": "question_end",
        "correct_option_ids": correct_ids,
        "leaderboard": leaderboard,
    }


async def get_leaderboard(db: AsyncSession, room: Room) -> list[dict]:
    leaderboard_result = await db.execute(
        select(RoomParticipant)
        .where(RoomParticipant.room_id == room.id)
        .order_by(RoomParticipant.score.desc())
    )
    participants = list(leaderboard_result.scalars().all())
    return [{"display_name": item.display_name, "score": item.score} for item in participants]


async def finish_question(db: AsyncSession, room: Room, question: Question) -> None:
    payload = await question_end_payload(db, room, question)
    await room_manager.broadcast(room.join_code, payload)
    await room_manager.broadcast(
        room.join_code,
        {"event": "leaderboard_update", "leaderboard": payload["leaderboard"]},
    )


async def schedule_question_end(room: Room, question: Question, seconds: int) -> None:
    async with AsyncSessionLocal() as db:
        await asyncio.sleep(seconds)
        await finish_question(db, room, question)
