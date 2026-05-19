import uuid
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(unique=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    is_admin: Mapped[bool] = mapped_column(default=False)

    # Relationships
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="owner")
    rooms_owned: Mapped[list["Room"]] = relationship(back_populates="owner")
    participations: Mapped[list["RoomParticipant"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")