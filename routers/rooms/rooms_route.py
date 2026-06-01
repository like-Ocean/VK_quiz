import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import get_current_user, get_current_user_optional
from models.user import User
from schemas.auth import MessageResponse
from schemas.room import (
    RoomCreate, RoomResponse, RoomJoin,
    RoomJoinResponse, ParticipantResponse,
    KickRequest, LeaderboardEntry
)
from services.room_service import (
    create_room, get_room_by_join_code, join_room,
    list_participants, kick_participant,
    get_room_results, get_room
)

room_router = APIRouter(prefix="/rooms", tags=["rooms"])


@room_router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room_handler(
    payload: RoomCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomResponse:
    return await create_room(db, current_user, payload.quiz_id)


@room_router.post("/join", response_model=RoomJoinResponse)
async def join_room_handler(
    payload: RoomJoin, db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> RoomJoinResponse:
    room_id, participant_id, guest_token = await join_room(
        db, payload.join_code,
        current_user, payload.guest_name
    )
    room = await get_room(db, room_id)
    return RoomJoinResponse(
        room_id=room_id,
        participant_id=participant_id,
        guest_token=guest_token,
        join_code=room.join_code,
    )


@room_router.get("/by-code/{join_code}", response_model=RoomResponse)
async def get_room_by_join_code_endpoint(join_code: str, db: AsyncSession = Depends(get_db)) -> RoomResponse:
    room = await get_room_by_join_code(db, join_code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@room_router.get("/{room_id}", response_model=RoomResponse)
async def get_room_handler(room_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> RoomResponse:
    return await get_room(db, room_id)


@room_router.get("/{room_id}/participants", response_model=list[ParticipantResponse])
async def get_participants(room_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[ParticipantResponse]:
    return await list_participants(db, room_id)


@room_router.post("/{room_id}/kick", response_model=MessageResponse)
async def kick_participant_handler(
    room_id: uuid.UUID, payload: KickRequest,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> MessageResponse:
    await kick_participant(
        db, room_id, current_user,
        payload.participant_id,
        payload.reason_id,
        payload.comment,
    )
    return MessageResponse(message="Participant kicked")


@room_router.get("/{room_id}/results", response_model=list[LeaderboardEntry])
async def get_results(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[LeaderboardEntry]:
    participants = await get_room_results(db, room_id)
    return [
        LeaderboardEntry(
            participant_id=item.id,
            display_name=item.display_name,
            score=item.score,
        )
        for item in participants
    ]