import asyncio
import json
from datetime import datetime
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from core.database import AsyncSessionLocal
from helpers.ws import (
    load_participant,
    get_quiz, question_payload,
    schedule_question_end
)
from models.question import Question
from models.room import RoomStatus
from services.room_manager import room_manager
from services.room_service import (
    get_room_by_join_code, get_question_by_index, save_answer
)


async def handle_room_ws(websocket: WebSocket, join_code: str, subject_id) -> None:
    async with AsyncSessionLocal() as db:
        room = await get_room_by_join_code(db, join_code)
        if not room:
            await websocket.close(code=1008)
            return

        participant, user = await load_participant(db, room.id, subject_id)
        is_owner = user is not None and room.owner_id == user.id
        if not participant and not is_owner:
            await websocket.close(code=1008)
            return

        participant_id = str(participant.id) if participant else str(user.id)
        await room_manager.connect(join_code, websocket, participant_id)
        print(f"[WS] Connected: participant={participant_id}, is_owner={is_owner}, room={join_code}")

        state = room_manager._get_state(join_code)
        if participant and not is_owner:
            await room_manager.broadcast(
                join_code,
                {
                    "event": "participant_joined",
                    "display_name": participant.display_name,
                    "participant_count": len(state.connections) - 1,
                },
            )

        try:
            while True:
                raw = await websocket.receive_text()
                data = json.loads(raw)
                event = data.get("event")
                print(f"[WS] Event '{event}' from participant={participant_id}, room={join_code}")

                if event == "start_quiz":
                    if not is_owner and not (user and user.is_admin):
                        await room_manager.send_to(
                            participant_id, join_code,
                            {"event": "error", "detail": "Access denied"},
                        )
                        continue

                    # Гард от повторного старта
                    if room.status != RoomStatus.waiting:
                        print(f"[WS] start_quiz ignored — room {join_code} already {room.status}")
                        continue

                    print(f"[WS] Starting quiz for room {join_code}")
                    room.status = RoomStatus.active
                    if room.started_at is None:
                        room.started_at = datetime.utcnow()
                    await db.commit()
                    print(f"[WS] Room {join_code} status set to active")

                    quiz = await get_quiz(db, room.quiz_id)
                    question = await get_question_by_index(db, room.quiz_id, room.current_question_index)
                    if not question:
                        await room_manager.send_to(
                            participant_id, join_code,
                            {"event": "error", "detail": "No questions"},
                        )
                        continue

                    total_result = await db.execute(
                        select(Question).where(Question.quiz_id == room.quiz_id)
                    )
                    total = len(total_result.scalars().all())
                    payload = await question_payload(
                        db, question,
                        room.current_question_index,
                        total,
                        quiz.time_per_question,
                    )
                    await room_manager.broadcast(join_code, payload)
                    print(f"[WS] First question broadcasted for room {join_code}")

                    # Отменяем старый таймер только здесь при старте
                    if state.question_timer_task and not state.question_timer_task.done():
                        print(f"[WS] Cancelling existing timer for room {join_code}")
                        state.question_timer_task.cancel()

                    state.question_timer_task = asyncio.create_task(
                        schedule_question_end(room, question, quiz.time_per_question)
                    )
                    print(f"[WS] Timer task created for room {join_code}")

                elif event == "submit_answer":
                    if is_owner:
                        continue

                    # 1. Берём question_id из события
                    raw_qid = data.get("question_id")
                    if not raw_qid:
                        await room_manager.send_to(
                            participant_id,
                            join_code,
                            {"event": "error", "detail": "question_id is required"},
                        )
                        continue

                    try:
                        qid = uuid.UUID(raw_qid)
                    except ValueError:
                        await room_manager.send_to(
                            participant_id,
                            join_code,
                            {"event": "error", "detail": "Invalid question_id"},
                        )
                        continue

                    # 2. Ищем конкретный вопрос этой викторины
                    result = await db.execute(
                        select(Question)
                        .options(selectinload(Question.answer_options))
                        .where(Question.id == qid, Question.quiz_id == room.quiz_id)
                    )
                    question = result.scalar_one_or_none()

                    if not question:
                        await room_manager.send_to(
                            participant_id,
                            join_code,
                            {"event": "error", "detail": "Question not found"},
                        )
                        continue

                    # 3. Сохраняем ответ
                    selected_ids = [str(item) for item in data.get("option_ids", [])]
                    print(f"[WS] Saving answer from {participant_id} for question {question.id}")
                    await save_answer(db, room, participant, question, selected_ids)

                    owner_id_str = str(room.owner_id)
                    await room_manager.send_to(
                        owner_id_str,
                        join_code,
                        {
                            "event": "participant_answered",
                            "participant_id": str(participant.id),
                            "display_name": participant.display_name,
                        },
                    )

        except WebSocketDisconnect:
            print(f"[WS] Disconnected: participant={participant_id}, room={join_code}")
            await room_manager.disconnect(join_code, participant_id)