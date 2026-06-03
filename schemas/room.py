from datetime import datetime
import uuid
from pydantic import BaseModel, Field
from models.room import RoomStatus


class RoomCreate(BaseModel):
    quiz_id: uuid.UUID


class RoomResponse(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    owner_id: uuid.UUID
    join_code: str
    status: RoomStatus
    current_question_index: int
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    class Config:
        from_attributes = True


class RoomJoin(BaseModel):
    join_code: str = Field(..., min_length=6, max_length=8)
    guest_name: str | None = Field(None, min_length=1, max_length=100)


class RoomJoinResponse(BaseModel):
    room_id: uuid.UUID
    participant_id: uuid.UUID
    guest_token: str | None = None
    join_code: str


class ParticipantResponse(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    user_id: uuid.UUID | None
    guest_name: str | None
    display_name: str
    score: int
    joined_at: datetime

    class Config:
        from_attributes = True


class KickRequest(BaseModel):
    participant_id: uuid.UUID
    reason_id: uuid.UUID | None = None
    comment: str | None = Field(None, max_length=500)


class LeaderboardEntry(BaseModel):
    participant_id: uuid.UUID
    display_name: str
    score: int


class ParticipationHistoryResponse(BaseModel):
    room_id: uuid.UUID
    quiz_title: str
    score: int
    total_points: int
    finished_at: datetime | None
    leaderboard_position: int | None
    total_participants: int
    questions_count: int
    time_per_question: int
    category: str | None 


class ImageUploadResponse(BaseModel):
    image_url: str
