import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASS = os.getenv("MYSQL_PASS")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")

if not all([MYSQL_USER, MYSQL_PASS, MYSQL_DB]):
    raise EnvironmentError("MYSQL_USER, MYSQL_PASS, and MYSQL_DB must be set in .env")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
    echo=False,
    connect_args={
        "connect_timeout": 30,
        "read_timeout": 30,
        "write_timeout": 30,
        "charset": "utf8mb4"
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
