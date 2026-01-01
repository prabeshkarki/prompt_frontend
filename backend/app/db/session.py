# app/db/session.py
from __future__ import annotations

from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

DATABASE_URL = settings.database_url
if not DATABASE_URL:
    # fallback build
    DATABASE_URL = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_pass}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_db}"
    )

connect_args: dict[str, Any] = {
    "connect_timeout": 30,
    "charset": "utf8mb4",
}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
    echo=settings.sql_echo,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()