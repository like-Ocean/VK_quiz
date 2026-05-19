import enum
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class RoomStatus(str, enum.Enum):
    waiting = "waiting"
    active = "active"
    finished = "finished"


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    join_code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    status: Mapped[RoomStatus] = mapped_column(default=RoomStatus.waiting)
    current_question_index: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]

    quiz: Mapped["Quiz"] = relationship(back_populates="rooms")
    owner: Mapped["User"] = relationship(back_populates="rooms_owned")
    participants: Mapped[list["RoomParticipant"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    answers: Mapped[list["ParticipantAnswer"]] = relationship(back_populates="room")