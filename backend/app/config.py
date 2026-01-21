from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def must_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def opt_env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v is not None and v != "" else default


@dataclass(frozen=True)
class Settings:
    # DB
    mysql_user: str
    mysql_pass: str
    mysql_db: str
    mysql_host: str
    mysql_port: str
    database_url: str
    sqlalchemy_echo: bool
    dev_create_tables: bool

    # Gemini
    gemini_api_key: str
    gemini_model: str
    gemini_embed_model: str

    # Qdrant
    qdrant_url: str
    qdrant_collection: str

    # RAG
    rag_top_k: int
    rag_min_score: float


def get_settings() -> Settings:
    mysql_user = opt_env("MYSQL_USER", "")
    mysql_pass = opt_env("MYSQL_PASS", "")
    mysql_db = opt_env("MYSQL_DB", "")
    mysql_host = opt_env("MYSQL_HOST", "localhost")
    mysql_port = opt_env("MYSQL_PORT", "3306")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        if not (mysql_user and mysql_pass and mysql_db):
            raise RuntimeError("Set DATABASE_URL or MYSQL_USER/MYSQL_PASS/MYSQL_DB")
        database_url = (
            f"mysql+pymysql://{mysql_user}:{mysql_pass}@{mysql_host}:{mysql_port}/{mysql_db}"
        )

    gemini_api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("GENAI_API_KEY")
        or ""
    )
    if not gemini_api_key:
        raise RuntimeError("Set GEMINI_API_KEY (or GOOGLE_API_KEY/GENAI_API_KEY)")

    return Settings(
        mysql_user=mysql_user,
        mysql_pass=mysql_pass,
        mysql_db=mysql_db,
        mysql_host=mysql_host,
        mysql_port=mysql_port,
        database_url=database_url,
        sqlalchemy_echo=opt_env("SQLALCHEMY_ECHO", "0") == "1",
        dev_create_tables=opt_env("DEV_CREATE_TABLES", "0") == "1",
        gemini_api_key=gemini_api_key,
        gemini_model=opt_env("GEMINI_MODEL", "gemini-2.0-flash"),
        gemini_embed_model=opt_env("GEMINI_EMBED_MODEL", "text-embedding-004"),
        qdrant_url=opt_env("QDRANT_URL", "http://localhost:6333"),
        qdrant_collection=opt_env("QDRANT_COLLECTION", "products"),
        rag_top_k=int(opt_env("RAG_TOP_K", "8")),
        rag_min_score=float(opt_env("RAG_MIN_SCORE", "0.25")),
    )