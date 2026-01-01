# app/schemas/chat.py
from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field, field_validator


class CreateSessionResponse(BaseModel):
    session_id: str = Field(..., description="UUID string for the chat session")


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="UUID string for the chat session")
    message: str = Field(..., min_length=1, max_length=1000)

    @field_validator("session_id")
    def validate_uuid(cls, value: str) -> str:
        try:
            uuid.UUID(value)
        except ValueError as exc:
            raise ValueError("session_id must be a valid UUID string") from exc
        return value


class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    bot_message: str

    product_id: int | None = None

    human_flag_active: bool = False
    human_flag_status: str = "tracking"   # tracking | active | closed
    human_flag_streak: int = 0


class ChatHistoryOut(BaseModel):
    id: str
    role: str = Field(..., min_length=1, max_length=20)
    message: str = Field(..., min_length=1)
    created_at: Optional[datetime] = None

    model_config = {
    "from_attributes": True
    }
