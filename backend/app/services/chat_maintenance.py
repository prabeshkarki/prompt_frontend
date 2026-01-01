# app/services/chat_maintenance.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models import ChatHistory, ChatSession, HumanFlag


def trim_chat_history(db: Session, session_id: str, max_messages: int = 50) -> None:
    """
    Keep only latest `max_messages` rows in chat_history for this session.
    """
    if max_messages <= 0:
        return

    # get ids to delete (older than newest max_messages)
    old_ids = (
        db.query(ChatHistory.id)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.desc())
        .offset(max_messages)
        .all()
    )
    if not old_ids:
        return

    old_ids_list = [row[0] for row in old_ids]
    db.query(ChatHistory).filter(ChatHistory.id.in_(old_ids_list)).delete(synchronize_session=False)
    db.commit()

    logger.info("Trimmed chat history session=%s deleted=%d", session_id, len(old_ids_list))


def trim_chat_sessions(db: Session, max_sessions: int = 20, keep_session_id: str | None = None) -> None:
    """
    Keep only latest `max_sessions` sessions by created_at.
    Will not delete `keep_session_id` if provided.
    Deletes HumanFlag rows for deleted sessions to avoid FK issues.
    """
    if max_sessions <= 0:
        return

    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    if len(sessions) <= max_sessions:
        return

    to_delete = sessions[max_sessions:]  # older sessions
    if keep_session_id:
        to_delete = [s for s in to_delete if s.session_id != keep_session_id]

    if not to_delete:
        return

    deleted_count = 0
    for s in to_delete:
        # delete flags first (chat history is cascaded via relationship on ChatSession)
        db.query(HumanFlag).filter(HumanFlag.session_id == s.session_id).delete(synchronize_session=False)

        db.delete(s)
        deleted_count += 1

    db.commit()
    logger.info("Trimmed chat sessions deleted=%d", deleted_count)