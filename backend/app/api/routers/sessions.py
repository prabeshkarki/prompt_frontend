# app/api/routers/sessions.py
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import ChatSession
from app.schemas import CreateSessionResponse
from app.services.chat_maintenance import trim_chat_sessions

router = APIRouter(tags=["sessions"])


@router.post("/create_session", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(db: Session = Depends(get_db)) -> CreateSessionResponse:
    session_id = str(uuid.uuid4())
    new_session = ChatSession(session_id=session_id, created_at=datetime.utcnow())
    trim_chat_sessions(db, max_sessions=200, keep_session_id=session_id)
    db.add(new_session)
    db.commit()
    return CreateSessionResponse(session_id=session_id)