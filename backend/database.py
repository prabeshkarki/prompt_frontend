from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool  # Add this import
import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASS = os.getenv("MYSQL_PASS")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,           # Checks connection before using
    pool_recycle=3600,            # Recycles connections every hour
    pool_size=5,                  # Reduced pool size
    max_overflow=10,              # Maximum overflow connections
    echo=False,                   # Set to True for debugging SQL queries
    connect_args={
        "connect_timeout": 30,    # Increase connection timeout
        "read_timeout": 30,       # Increase read timeout  
        "write_timeout": 30,      # Increase write timeout
        "charset": "utf8mb4"      # Specify charset
    }
)

# Alternative: If above doesn't work, try disabling connection pooling:
# engine = create_engine(
#     DATABASE_URL,
#     poolclass=NullPool,  # Disable connection pooling
#     echo=True,
#     connect_args={
#         "connect_timeout": 30,
#         "charset": "utf8mb4"
#     }
# )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()