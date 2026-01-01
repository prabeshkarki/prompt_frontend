from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HumanFlag(Base):
    __tablename__ = "human_flags"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("chat_sessions.session_id"),
        nullable=False,
        index=True,
        unique=True,
    )

    # tracking | active | closed
    status: Mapped[str] = mapped_column(String(20), default="tracking", nullable=False, index=True)

    # counts consecutive exact-product failures
    no_match_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_user_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)