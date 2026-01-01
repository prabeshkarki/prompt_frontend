# app/models/product.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    screen: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    processor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ram: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    storage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    camera: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)