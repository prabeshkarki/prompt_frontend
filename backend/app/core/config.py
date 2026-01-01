# app/core/config.py
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)


def _parse_origins(raw: str | None) -> list[str]:
    raw = (raw or "").strip()
    if raw in ("", "*"):
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


@dataclass(frozen=True)
class Settings:
    # DB
    database_url: str = os.getenv("DATABASE_URL", "")
    mysql_user: str = os.getenv("MYSQL_USER", "")
    mysql_pass: str = os.getenv("MYSQL_PASS", "")
    mysql_db: str = os.getenv("MYSQL_DB", "")
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: str = os.getenv("MYSQL_PORT", "3306")
    sql_echo: bool = os.getenv("SQL_ECHO", "false").lower() == "true"

    # Gemini
    gemini_api_key: str = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("GENAI_API_KEY")
        or ""
    )
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # CORS (fixed: no mutable default)
    cors_allow_origins: list[str] = field(
        default_factory=lambda: _parse_origins(os.getenv("CORS_ALLOW_ORIGINS", "*"))
    )


settings = Settings()