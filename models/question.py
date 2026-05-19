import enum
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class QuestionType(str, enum.Enum):
    text = "text"
    image = "image"


class AnswerType(str, enum.Enum):
    single = "single"
    multiple = "multiple"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    order: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None]
    question_type: Mapped[QuestionType] = mapped_column(default=QuestionType.text)
    answer_type: Mapped[AnswerType] = mapped_column(default=AnswerType.single)
    points: Mapped[int] = mapped_column(default=100)

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
    answer_options: Mapped[list["AnswerOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    participant_answers: Mapped[list["ParticipantAnswer"]] = relationship(
        back_populates="question"
    )