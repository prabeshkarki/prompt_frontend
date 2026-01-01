# import os
# from typing import Generator

# from dotenv import load_dotenv
# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session, declarative_base, sessionmaker

# # Load environment variables from .env
# load_dotenv()

# # --------------------------------------------------------------------------- #
# # Environment configuration
# # --------------------------------------------------------------------------- #

# def _get_env_var(name: str, default: str | None = None) -> str:
#     """Return environment variable or raise if not found and no default."""
#     value = os.getenv(name, default)
#     if value is None:
#         raise EnvironmentError(f"{name} must be set in .env")
#     return value

# MYSQL_USER = _get_env_var("MYSQL_USER")
# MYSQL_PASS = _get_env_var("MYSQL_PASS")
# MYSQL_DB   = _get_env_var("MYSQL_DB")
# MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
# MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")

# # Build DATABASE_URL if not explicitly set
# DATABASE_URL = os.getenv("DATABASE_URL")
# if not DATABASE_URL:
#     DATABASE_URL = (
#         f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
#     )

# # Connection arguments for PyMySQL
# connect_args: dict[str, str | int] = {
#     "connect_timeout": 30,
#     "charset": "utf8mb4",
# }

# # --------------------------------------------------------------------------- #
# # SQLAlchemy engine and session
# # --------------------------------------------------------------------------- #

# engine = create_engine(
#     DATABASE_URL,
#     pool_pre_ping=True,
#     pool_recycle=3600,
#     pool_size=5,
#     max_overflow=10,
#     echo=True,  # set to False in production
#     connect_args=connect_args,
# )

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # --------------------------------------------------------------------------- #
# # Dependency for FastAPI
# # --------------------------------------------------------------------------- #

# def get_db() -> Generator[Session, None, None]:
#     """FastAPI dependency that provides a database session."""
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
