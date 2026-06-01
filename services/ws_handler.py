import asyncio
import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
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

                if event == "start_quiz":
                    if not is_owner and not (user and user.is_admin):
                        await room_manager.send_to(
                            participant_id, join_code,
                            {"event": "error", "detail": "Access denied"},
                        )
                        continue

                    room.status = RoomStatus.active
                    if room.started_at is None:
                        room.started_at = datetime.utcnow()
                    await db.commit()

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

                    if state.question_timer_task:
                        state.question_timer_task.cancel()
                    state.question_timer_task = asyncio.create_task(
                        schedule_question_end(room, question, quiz.time_per_question)
                    )

                elif event == "submit_answer":
                    if is_owner:
                        continue

                    question = await get_question_by_index(db, room.quiz_id, room.current_question_index)
                    if not question:
                        await room_manager.send_to(
                            participant_id, join_code,
                            {"event": "error", "detail": "Question not found"},
                        )
                        continue

                    selected_ids = [str(item) for item in data.get("option_ids", [])]
                    await save_answer(db, room, participant, question, selected_ids)

                    owner_id_str = str(room.owner_id)
                    await room_manager.send_to(
                        owner_id_str, join_code,
                        {
                            "event": "participant_answered",
                            "participant_id": str(participant.id),
                            "display_name": participant.display_name,
                        },
                    )

        except WebSocketDisconnect:
            await room_manager.disconnect(join_code, participant_id)