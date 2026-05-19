import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class ParticipantAnswer(Base):
    __tablename__ = "participant_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), index=True
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("room_participants.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    selected_option_ids: Mapped[str]
    is_correct: Mapped[bool] = mapped_column(default=False)
    score_earned: Mapped[int] = mapped_column(default=0)
    answered_at: Mapped[datetime] = mapped_column(default=func.now())

    room: Mapped["Room"] = relationship(back_populates="answers")
    participant: Mapped["RoomParticipant"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship(back_populates="participant_answers")