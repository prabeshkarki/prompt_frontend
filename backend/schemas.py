# from datetime import datetime
# from typing import Optional
# import uuid

# from pydantic import BaseModel, Field, validator


# class CreateSessionResponse(BaseModel):
#     session_id: str = Field(..., description="UUID string for the chat session")


# class ChatRequest(BaseModel):
#     session_id: str = Field(..., description="UUID string for the chat session")
#     message: str = Field(..., min_length=1, max_length=1000)

#     @validator("session_id")
#     def validate_uuid(cls, value: str) -> str:
#         try:
#             uuid.UUID(value)
#         except ValueError as exc:
#             raise ValueError("session_id must be a valid UUID string") from exc
#         return value


# class ChatResponse(BaseModel):
#     session_id: str
#     user_message: str
#     bot_message: str

# class ChatHistoryOut(BaseModel):
#     id: str
#     role: str = Field(..., min_length=1, max_length=20)
#     message: str = Field(..., min_length=1)
#     created_at: Optional[datetime] = None

#     class Config:
#         orm_mode = True


# class ProductBase(BaseModel):
#     name: str = Field(..., min_length=3, max_length=255)
#     # description: Optional[str] = Field(None, max_length=1000)
#     category: Optional[str] = Field(None, max_length=50)
#     brand: Optional[str] = Field(None, max_length=100)
#     screen: Optional[str] = Field(None, max_length=100)
#     processor: Optional[str] = Field(None, max_length=100)
#     ram: Optional[str] = Field(None, max_length=50)
#     storage: Optional[str] = Field(None, max_length=100)
#     camera: Optional[str] = Field(None, max_length=100)
#     price: float = Field(..., gt=0, description="Price must be greater than 0")


# class ProductOut(ProductBase):
#     id: int
#     created_at: Optional[datetime] = None

#     class Config:
#         orm_mode = True

# class UserProductHistoryOut(BaseModel):
#     id: str
#     session_id: str
#     product_id: int
#     product_name: str
#     category: Optional[str]
#     brand: Optional[str]
#     screen: Optional[str]
#     processor: Optional[str]
#     ram: Optional[str]
#     storage: Optional[str]
#     camera: Optional[str]
#     price: float
#     # created_at: Optional[datetime] = None

#     class Config:
#         orm_mode = True