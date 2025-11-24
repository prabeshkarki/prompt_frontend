from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CreateSessionResponse(BaseModel):
    session_id: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    bot_message: str

class ChatHistoryOut(BaseModel):
    id: str
    role: str
    message: str
    created_at: datetime

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[str] = None

class ProductOut(ProductBase):
    id: str
    created_at: datetime

    class Config:
        orm_made = True