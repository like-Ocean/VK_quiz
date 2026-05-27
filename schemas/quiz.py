from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class QuizCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    category_id: uuid.UUID | None = None
    time_per_question: int = Field(30, ge=5, le=300)
    is_public: bool = True


class QuizUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    category_id: uuid.UUID | None = None
    time_per_question: int | None = Field(None, ge=5, le=300)
    is_public: bool | None = None


class QuizResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    category_id: uuid.UUID | None
    title: str
    description: str | None
    time_per_question: int
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
