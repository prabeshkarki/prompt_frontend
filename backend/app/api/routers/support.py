from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import ChatHistory, ChatSession, HumanFlag

router = APIRouter(prefix="/support", tags=["support"])


class SupportMessageIn(BaseModel):
    session_id: str
    message: str


@router.get("/queue")
def queue(db: Session = Depends(get_db)):
    flags = db.query(HumanFlag).filter(HumanFlag.status == "active").order_by(HumanFlag.updated_at.desc()).all()
    return [{"flag_id": f.id, "session_id": f.session_id, "reason": f.reason, "updated_at": f.updated_at.isoformat()} for f in flags]


@router.post("/send")
def send_support_message(data: SupportMessageIn, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.session_id == data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msg = data.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    db.add(ChatHistory(
        session_id=data.session_id,
        role="assistant",  # will show as "Bot" on your frontend; good enough
        message=msg,
        created_at=datetime.utcnow(),
    ))
    db.commit()
    return {"ok": True}