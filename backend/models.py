# from __future__ import annotations

# import uuid
# from datetime import datetime
# from typing import Optional
# from sqlalchemy import DateTime,Float,ForeignKey,Integer,String,Text
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from database import Base


# class Product(Base):
#     __tablename__ = "products"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
#     name: Mapped[str] = mapped_column(String(255), nullable=False)
#     # description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

#     category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
#     brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
#     screen: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
#     processor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
#     ram: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
#     storage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
#     camera: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


#     price: Mapped[float] = mapped_column(Float, nullable=False)
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime, default=datetime.utcnow, nullable=False
#     )


# class ChatSession(Base):
#     __tablename__ = "chat_sessions"

#     session_id: Mapped[str] = mapped_column(
#         String(64),
#         primary_key=True,
#         index=True,
#         default=lambda: str(uuid.uuid4()),
#     )
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime, default=datetime.utcnow, nullable=False
#     )
#     messages: Mapped[list["ChatHistory"]] = relationship(
#         "ChatHistory",
#         back_populates="session",
#         cascade="all, delete-orphan",
#     )
#     product_history: Mapped[list["UserProductHistory"]] = relationship(
#         "UserProductHistory",
#         back_populates="session",
#         cascade="all, delete-orphan",
#     )


# class ChatHistory(Base):
#     __tablename__ = "chat_history"

#     id: Mapped[str] = mapped_column(
#         String(64), primary_key=True, default=lambda: str(uuid.uuid4())
#     )
#     session_id: Mapped[str] = mapped_column(
#         String(64),
#         ForeignKey("chat_sessions.session_id"),
#         nullable=False,
#         index=True,
#     )
#     role: Mapped[str] = mapped_column(String(20), nullable=False)
#     message: Mapped[str] = mapped_column(Text, nullable=False)
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime, default=datetime.utcnow, nullable=False, index=True
#     )

#     session: Mapped["ChatSession"] = relationship(
#         "ChatSession",
#         back_populates="messages",
#     )

# class UserProductHistory(Base):
#     __tablename__ = "user_product_history"

#     id: Mapped[int] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
#     session_id: Mapped[str] = mapped_column(
#         String(64),
#         ForeignKey("chat_sessions.session_id"),
#         nullable=False,
#         index=True,
#     )
#     product_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey("products.id"),
#         nullable=False,
#         index=True,
#     )
#     product_name: Mapped[str] = mapped_column(String(255), nullable=False)
#     # created_at: Mapped[datetime] = mapped_column(
#     #     DateTime, default=datetime.utcnow, nullable=False, index=True
#     # )
#     session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="product_history",)
#     # product: Mapped["Product"] = relationship("Product")
