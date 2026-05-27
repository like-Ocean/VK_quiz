import uuid
from pydantic import BaseModel, Field
from models.question import QuestionType, AnswerType


class AnswerOptionCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    is_correct: bool = False


class AnswerOptionUpdate(BaseModel):
    id: uuid.UUID | None = None
    text: str | None = Field(None, min_length=1, max_length=500)
    is_correct: bool | None = None


class AnswerOptionResponse(BaseModel):
    id: uuid.UUID
    text: str
    is_correct: bool

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    order: int = Field(..., ge=0)
    text: str = Field(..., min_length=1)
    image_url: str | None = None
    question_type: QuestionType = QuestionType.text
    answer_type: AnswerType = AnswerType.single
    points: int = Field(100, ge=0)
    answer_options: list[AnswerOptionCreate]


class QuestionUpdate(BaseModel):
    order: int | None = Field(None, ge=0)
    text: str | None = Field(None, min_length=1)
    image_url: str | None = None
    question_type: QuestionType | None = None
    answer_type: AnswerType | None = None
    points: int | None = Field(None, ge=0)
    answer_options: list[AnswerOptionUpdate] | None = None


class QuestionResponse(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    order: int
    text: str
    image_url: str | None
    question_type: QuestionType
    answer_type: AnswerType
    points: int
    answer_options: list[AnswerOptionResponse]

    class Config:
        from_attributes = True


class QuestionReorderRequest(BaseModel):
    question_ids: list[uuid.UUID]
