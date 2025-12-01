from pydantic import BaseModel, Field, validator, condecimal
from datetime import datetime
from typing import Optional
import uuid

class CreateSessionResponse(BaseModel):
    session_id: str = Field(..., description="UUID string for the chat session")

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="UUID string for the chat session")
    message: str = Field(..., min_length=1, max_length=1000)

    @validator("session_id")
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("session_id must be a valid UUID string")
        return v

class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    bot_message: str

class ChatHistoryOut(BaseModel):
    id: str
    role: str = Field(..., min_length=1, max_length=20)
    message: str = Field(..., min_length=1)
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0, description="Price must be greater than 0")

class ProductOut(ProductBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
