from datetime import datetime
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class ParticipantAnswer(Base):
    __tablename__ = "participant_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("room_participants.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    selected_option_ids: Mapped[str]
    is_correct: Mapped[bool] = mapped_column(default=False)
    score_earned: Mapped[int] = mapped_column(default=0)
    answered_at: Mapped[datetime] = mapped_column(default=func.now())

    room: Mapped["Room"] = relationship(back_populates="answers")
    participant: Mapped["RoomParticipant"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship(back_populates="participant_answers")