import asyncio
import uuid
from datetime import datetime, timezone
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

    print(f"[TIMER] Started for room {room_id}, question {question_id}, sleeping {seconds}s")

    try:
        await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        print(f"[TIMER] Cancelled during sleep for room {room_id}")
        return

    print(f"[TIMER] Woke up for room {room_id}, running finish_question")

    # Шаг 1 — отправляем question_end и leaderboard_update
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Question).options(selectinload(Question.answer_options))
                .where(Question.id == question_id)
            )
            fresh_question = result.scalar_one()

            result = await db.execute(select(Room).where(Room.id == room_id))
            fresh_room = result.scalar_one()

            print(f"[TIMER] Sending question_end for room {room_id}")
            await finish_question(db, fresh_room, fresh_question)
            print(f"[TIMER] question_end sent for room {room_id}")
    except Exception as e:
        print(f"[TIMER] ERROR in finish_question for room {room_id}: {e}")
        return

    print(f"[TIMER] Sleeping 3s before next question for room {room_id}")
    try:
        await asyncio.sleep(3)
    except asyncio.CancelledError:
        print(f"[TIMER] Cancelled during 3s pause for room {room_id}")
        return

    print(f"[TIMER] Advancing question index for room {room_id}")

    # Шаг 2 — увеличиваем индекс и решаем: следующий вопрос или финал
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Room).where(Room.id == room_id))
            fresh_room = result.scalar_one()
            print(f"[TIMER] Current index: {fresh_room.current_question_index}, status: {fresh_room.status}")

            new_index = fresh_room.current_question_index + 1

            await db.execute(
                update(Room)
                .where(Room.id == room_id)
                .values(current_question_index=new_index)
            )
            await db.commit()
            print(f"[TIMER] Index updated to {new_index} for room {room_id}")

            next_question = await get_question_by_index(db, quiz_id, new_index)
            print(f"[TIMER] Next question at index {new_index}: {'found' if next_question else 'NOT FOUND — finishing'}")

            if not next_question:
                # Финал — отдельный коммит, защищён от отмены
                print(f"[TIMER] Finishing room {room_id}")
                await db.execute(
                    update(Room)
                    .where(Room.id == room_id)
                    .values(
                        status=RoomStatus.finished,
                        finished_at=datetime.now(),
                    )
                )
                await db.commit()
                print(f"[TIMER] Room {room_id} marked as finished in DB ✓")

                result = await db.execute(select(Room).where(Room.id == room_id))
                fresh_room_for_lb = result.scalar_one()
                leaderboard = await get_leaderboard(db, fresh_room_for_lb)

        # broadcast вне async with — DB уже закрыта, статус записан
        if not next_question:
            print(f"[TIMER] Broadcasting quiz_finish for room {room_id}")
            await room_manager.broadcast(
                join_code,
                {"event": "quiz_finish", "leaderboard": leaderboard}
            )
            print(f"[TIMER] quiz_finish broadcasted for room {room_id} ✓")
            return

        # Следующий вопрос
        async with AsyncSessionLocal() as db:
            quiz = await get_quiz(db, quiz_id)
            total_result = await db.execute(
                select(Question).where(Question.quiz_id == quiz_id)
            )
            total = len(total_result.scalars().all())

            payload = await question_payload(db, next_question, new_index, total, quiz.time_per_question)

            result = await db.execute(select(Room).where(Room.id == room_id))
            fresh_room_for_next = result.scalar_one()

        print(f"[TIMER] Broadcasting next question (index {new_index}) for room {room_id}")
        await room_manager.broadcast(join_code, payload)

        # Запускаем новый таймер — НЕ отменяем текущий (мы и есть текущий)
        state = room_manager._get_state(join_code)
        print(f"[TIMER] Scheduling next timer for room {room_id}, index {new_index}")
        state.question_timer_task = asyncio.create_task(
            schedule_question_end(fresh_room_for_next, next_question, quiz.time_per_question)
        )
        print(f"[TIMER] Next timer scheduled for room {room_id} ✓")

    except asyncio.CancelledError:
        print(f"[TIMER] CancelledError caught during DB finalization for room {room_id} — ignoring")
    except Exception as e:
        print(f"[TIMER] ERROR during question advance for room {room_id}: {e}")