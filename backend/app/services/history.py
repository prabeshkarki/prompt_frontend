# app/services/history.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import ChatHistory, ChatSession


def trim_chat_history(db: Session, session_id: str, max_messages: int = 20) -> None:
    messages = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.desc())
        .all()
    )
    if len(messages) <= max_messages:
        return
    for msg in messages[max_messages:]:
        db.delete(msg)
    db.commit()


def trim_chat_sessions(db: Session, max_sessions: int = 50) -> None:
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    if len(sessions) <= max_sessions:
        return
    for s in sessions[max_sessions:]:
        db.delete(s)
    db.commit()


def summarize_history_for_prompt(history: list[ChatHistory], max_chars: int = 1200) -> str:
    if not history:
        return "none"
    lines: list[str] = []
    for m in history[-12:]:
        role = "U" if m.role == "user" else "A"
        msg = (m.message or "").strip().replace("\n", " ")
        if len(msg) > 220:
            msg = msg[:220] + "…"
        lines.append(f"{role}: {msg}")
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[-max_chars:]
    return text