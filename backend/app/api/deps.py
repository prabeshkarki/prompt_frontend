# app/api/deps.py
from app.db.session import get_db

__all__ = ["get_db"]