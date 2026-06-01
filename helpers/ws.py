import asyncio
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from core.database import AsyncSessionLocal
from models.question import Question
from models.quiz import Quiz
from models.room import Room, RoomStatus
from models.room_participant import RoomParticipant
from models.user import User
from services.room_manager import room_manager
from services.room_service import get_question_by_index


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
        .where(
            RoomParticipant.room_id == room.id,
            RoomParticipant.user_id != room.owner_id,
        )
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
    room_id = room.id
    join_code = room.join_code
    quiz_id = room.quiz_id
    question_id = question.id

    await asyncio.sleep(seconds)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Question).options(selectinload(Question.answer_options))
            .where(Question.id == question_id)
        )
        fresh_question = result.scalar_one()

        result = await db.execute(select(Room).where(Room.id == room_id))
        fresh_room = result.scalar_one()

        await finish_question(db, fresh_room, fresh_question)

    await asyncio.sleep(3)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Room).where(Room.id == room_id))
        fresh_room = result.scalar_one()

        new_index = fresh_room.current_question_index + 1

        await db.execute(
            update(Room)
            .where(Room.id == room_id)
            .values(current_question_index=new_index)
        )
        await db.commit()

        next_question = await get_question_by_index(db, quiz_id, new_index)

        if not next_question:
            from datetime import datetime, timezone
            await db.execute(
                update(Room)
                .where(Room.id == room_id)
                .values(
                    status=RoomStatus.finished,
                    finished_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()

            result = await db.execute(select(Room).where(Room.id == room_id))
            fresh_room_for_lb = result.scalar_one()

            leaderboard = await get_leaderboard(db, fresh_room_for_lb)
            await room_manager.broadcast(
                join_code,
                {"event": "quiz_finish", "leaderboard": leaderboard}
            )
            return

        quiz = await get_quiz(db, quiz_id)
        total_result = await db.execute(
            select(Question).where(Question.quiz_id == quiz_id)
        )
        total = len(total_result.scalars().all())

        payload = await question_payload(
            db, next_question,
            new_index,
            total, quiz.time_per_question,
        )
        await room_manager.broadcast(join_code, payload)

        result = await db.execute(select(Room).where(Room.id == room_id))
        fresh_room_for_next = result.scalar_one()

        state = room_manager._get_state(join_code)
        if state.question_timer_task:
            state.question_timer_task.cancel()
        state.question_timer_task = asyncio.create_task(
            schedule_question_end(fresh_room_for_next, next_question, quiz.time_per_question)
        )