# app/api/routers/history.py
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import ChatHistory, ChatSession
from app.schemas import ChatHistoryOut

router = APIRouter(tags=["history"])


@router.get("/history/{session_id}", response_model=List[ChatHistoryOut])
def get_history(
    session_id: str = Path(..., description="Chat session UUID"),
    db: Session = Depends(get_db),
) -> List[ChatHistoryOut]:
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id format")

    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    if not history:
        return[]

    return [ChatHistoryOut.from_orm(msg) for msg in history]