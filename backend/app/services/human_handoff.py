from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session

from app.models import HumanFlag


def get_flag(db: Session, session_id: str) -> HumanFlag | None:
    return db.query(HumanFlag).filter(HumanFlag.session_id == session_id).first()


def get_or_create_flag(db: Session, session_id: str) -> HumanFlag:
    flag = get_flag(db, session_id)
    if flag:
        return flag

    flag = HumanFlag(session_id=session_id, status="tracking", no_match_streak=0)
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag


def reset_streak(db: Session, session_id: str) -> None:
    flag = get_flag(db, session_id)
    if not flag:
        return
    if flag.no_match_streak != 0:
        flag.no_match_streak = 0
        flag.updated_at = datetime.utcnow()
        db.commit()


def increment_streak(db: Session, session_id: str, user_message: str) -> int:
    flag = get_or_create_flag(db, session_id)
    flag.no_match_streak = int(flag.no_match_streak or 0) + 1
    flag.last_user_message = user_message
    flag.updated_at = datetime.utcnow()
    db.commit()
    return flag.no_match_streak


def activate_flag(db: Session, session_id: str, reason: str, user_message: str) -> HumanFlag:
    flag = get_or_create_flag(db, session_id)
    now = datetime.utcnow()
    flag.status = "active"
    flag.reason = reason
    flag.last_user_message = user_message
    flag.activated_at = now
    flag.updated_at = now
    db.commit()
    db.refresh(flag)
    return flag