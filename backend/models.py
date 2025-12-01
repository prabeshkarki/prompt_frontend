import uuid
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Product(Base): 
    __tablename__ = "products" 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    session_id = Column(String(64), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("ChatHistory", back_populates="session")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(64), ForeignKey("chat_sessions.session_id"), nullable=False)
    role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    session = relationship("ChatSession", back_populates="messages")
