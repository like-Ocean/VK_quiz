import random
import string
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from core.security import create_access_token
from models.kick_reason import KickReason
from models.participant_answer import ParticipantAnswer
from models.question import Question
from models.quiz import Quiz
from models.room import Room, RoomStatus
from models.room_kick import RoomKick
from models.room_participant import RoomParticipant
from models.user import User
from helpers.quiz import _get_quiz, _get_room
from services.room_manager import room_manager
from services.score_service import check_answer, calculate_score


def generate_join_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


async def get_room(db: AsyncSession, room_id: uuid.UUID) -> Room:
    return await _get_room(db, room_id)


async def create_room(db: AsyncSession, user: User, quiz_id: uuid.UUID) -> Room:
    quiz = await _get_quiz(db, quiz_id)
    if quiz.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    join_code = generate_join_code()
    for _ in range(5):
        result = await db.execute(select(Room).where(Room.join_code == join_code))
        if not result.scalar_one_or_none():
            break
        join_code = generate_join_code()
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Join code error")

    room = Room(quiz_id=quiz_id, owner_id=user.id, join_code=join_code, status=RoomStatus.waiting)
    db.add(room)
    await db.commit()
    await db.refresh(room)

    return room


async def join_room(
    db: AsyncSession, join_code: str,
    user: User | None, guest_name: str | None
) -> tuple[uuid.UUID, uuid.UUID, str | None]:
    room = await get_room_by_join_code(db, join_code)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Room not found"
        )

    if user and user.is_admin:
        pass
    elif room.status != RoomStatus.waiting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Quiz already started"
        )

    if not user and not guest_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Guest name required"
        )

    if user:
        result = await db.execute(
            select(RoomParticipant).where(
                RoomParticipant.room_id == room.id,
                RoomParticipant.user_id == user.id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already in room")

    display_name = user.username if user else guest_name
    participant = RoomParticipant(
        room_id=room.id,
        user_id=user.id if user else None,
        guest_name=guest_name if not user else None,
        display_name=display_name
    )
    db.add(participant)
    await db.commit()
    await db.refresh(participant)

    guest_token = None
    if not user:
        guest_token = create_access_token(participant.id, expires_minutes=120)

    return room.id, participant.id, guest_token


async def list_participants(db: AsyncSession, room_id: uuid.UUID) -> list[RoomParticipant]:
    await _get_room(db, room_id)
    result = await db.execute(
        select(RoomParticipant).where(RoomParticipant.room_id == room_id)
    )
    return list(result.scalars().all())


async def kick_participant(
    db: AsyncSession, room_id: uuid.UUID,
    user: User, participant_id: uuid.UUID,
    reason_id: uuid.UUID | None, comment: str | None
) -> None:
    room = await _get_room(db, room_id)
    if room.owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    result = await db.execute(
        select(RoomParticipant).where(
            RoomParticipant.id == participant_id,
            RoomParticipant.room_id == room.id
        )
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")

    reason_label = "Другое"
    if reason_id:
        reason_result = await db.execute(select(KickReason).where(KickReason.id == reason_id))
        reason = reason_result.scalar_one_or_none()
        if not reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reason not found")
        reason_label = reason.label

    db.add(
        RoomKick(
            room_id=room.id,
            participant_id=participant.id,
            kicked_by=user.id,
            reason_id=reason_id,
            comment=comment
        )
    )
    await db.delete(participant)
    await db.commit()

    await room_manager.kick_participant(room.join_code, str(participant.id), reason_label)


async def get_room_results(db: AsyncSession, room_id: uuid.UUID) -> list[dict]:
    room = await _get_room(db, room_id)
    quiz_result = await db.execute(select(Quiz).where(Quiz.id == room.quiz_id))
    quiz = quiz_result.scalar_one()
    q_count_result = await db.execute(
        select(func.count(Question.id)).where(Question.quiz_id == quiz.id)
    )
    questions_count = q_count_result.scalar_one() or 0
    total_points_result = await db.execute(
        select(func.sum(Question.points)).where(Question.quiz_id == quiz.id)
    )
    total_points = total_points_result.scalar_one() or 0
    participants_result = await db.execute(
        select(RoomParticipant)
        .where(RoomParticipant.room_id == room_id)
        .order_by(RoomParticipant.score.desc())
    )
    participants = list(participants_result.scalars().all())
    items: list[dict] = []
    for p in participants:
        correct_result = await db.execute(
            select(func.count(ParticipantAnswer.id)).where(
                ParticipantAnswer.room_id == room_id,
                ParticipantAnswer.participant_id == p.id,
                ParticipantAnswer.is_correct == True,
            )
        )
        correct = correct_result.scalar_one() or 0
        items.append(
            {
                "participant_id": p.id,
                "display_name": p.display_name,
                "score": p.score,
                "total": total_points,
                "correct": correct,
                "questions": questions_count
            }
        )

    return items


async def get_room_by_join_code(db: AsyncSession, join_code: str) -> Room | None:
    result = await db.execute(select(Room).where(Room.join_code == join_code))
    return result.scalar_one_or_none()


async def get_question_by_index(db: AsyncSession, quiz_id: uuid.UUID, index: int) -> Question | None:
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.answer_options))
        .where(Question.quiz_id == quiz_id)
        .order_by(Question.order)
    )
    questions = list(result.scalars().all())
    if index < 0 or index >= len(questions):
        return None
    return questions[index]


async def save_answer(
    db: AsyncSession, room: Room,
    participant: RoomParticipant,
    question: Question, selected_option_ids: list[str]
) -> tuple[bool, int]:
    is_correct = check_answer(question, selected_option_ids)
    score = calculate_score(question, is_correct)

    db.add(
        ParticipantAnswer(
            room_id=room.id,
            participant_id=participant.id,
            question_id=question.id,
            selected_option_ids=",".join(selected_option_ids),
            is_correct=is_correct,
            score_earned=score
        )
    )
    participant.score += score
    await db.commit()
    return is_correct, score


async def get_kick_reasons(db: AsyncSession) -> list[KickReason]:
    result = await db.execute(select(KickReason))
    return result.scalars().all()