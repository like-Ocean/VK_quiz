import asyncio
from dataclasses import dataclass, field
from typing import Dict
from fastapi import WebSocket


@dataclass
class RoomState:
    connections: Dict[str, WebSocket] = field(default_factory=dict)
    question_timer_task: asyncio.Task | None = None


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, RoomState] = {}

    def _get_state(self, room_code: str) -> RoomState:
        if room_code not in self.rooms:
            self.rooms[room_code] = RoomState()
        return self.rooms[room_code]

    async def connect(self, room_code: str, websocket: WebSocket, participant_id: str) -> None:
        await websocket.accept()
        state = self._get_state(room_code)
        state.connections[participant_id] = websocket

    async def disconnect(self, room_code: str, participant_id: str) -> None:
        state = self._get_state(room_code)
        state.connections.pop(participant_id, None)
        # if not state.connections and state.question_timer_task:
        #     state.question_timer_task.cancel()
        #     state.question_timer_task = None

    async def broadcast(self, room_code: str, message: dict) -> None:
        state = self._get_state(room_code)
        for ws in list(state.connections.values()):
            await ws.send_json(message)

    async def send_to(self, participant_id: str, room_code: str, message: dict) -> None:
        state = self._get_state(room_code)
        ws = state.connections.get(participant_id)
        if ws:
            await ws.send_json(message)

    async def kick_participant(self, room_code: str, participant_id: str, reason: str) -> None:
        await self.send_to(participant_id, room_code, {"event": "kicked", "reason": reason})
        state = self._get_state(room_code)
        ws = state.connections.get(participant_id)
        if ws:
            await ws.close()
            state.connections.pop(participant_id, None)


room_manager = RoomManager()
