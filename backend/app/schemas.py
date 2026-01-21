from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateSessionResponse(BaseModel):
    session_id: str = Field(..., description="UUID string for the chat session")


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="UUID string for the chat session")
    message: str = Field(..., min_length=1, max_length=1000)

    @field_validator("session_id")
    @classmethod
    def validate_uuid(cls, value: str) -> str:
        uuid.UUID(value)
        return value


class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    bot_message: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    retrieved_product_ids: list[int] = Field(default_factory=list)
    debug: Optional[dict[str, Any]] = None


class ChatHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str = Field(..., min_length=1, max_length=20)
    message: str = Field(..., min_length=1)
    created_at: Optional[datetime] = None


class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    screen: Optional[str] = Field(None, max_length=100)
    processor: Optional[str] = Field(None, max_length=100)
    ram: Optional[str] = Field(None, max_length=50)
    storage: Optional[str] = Field(None, max_length=100)
    camera: Optional[str] = Field(None, max_length=100)
    price: float = Field(..., gt=0)


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: Optional[datetime] = None