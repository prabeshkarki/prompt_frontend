# app/api/routers/chat.py
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.logging import logger
from app.models import ChatHistory, ChatSession, Product
from app.schemas import ChatRequest, ChatResponse
from app.services.gemini_client import gemini_product_answer
from app.services.human_handoff import get_flag

from app.services.intent import detect_intent, Intent
from app.services.product_retrieval import retrieve_products_for_prompt, products_to_gemini_payload
from app.services.chat_maintenance import trim_chat_history, trim_chat_sessions

router = APIRouter(tags=["chat"])

_ID_PATTERN = re.compile(r"(?:^|\s)(?:#|id\s*[:#]?\s*|product\s+)(\d+)\b", re.IGNORECASE)


def store_assistant(db: Session, session_id: str, message: str) -> None:
    db.add(
        ChatHistory(
            session_id=session_id,
            role="assistant",
            message=message,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()


def build_response(db: Session, session_id: str, user_message: str, bot_message: str, product_id: int | None) -> ChatResponse:
    flag = get_flag(db, session_id)
    return ChatResponse(
        session_id=session_id,
        user_message=user_message,
        bot_message=bot_message,
        product_id=product_id,
        human_flag_active=bool(flag and flag.status == "active"),
        human_flag_status=(flag.status if flag else "tracking"),
        human_flag_streak=int(getattr(flag, "no_match_streak", 0)) if flag else 0,
    )


def extract_product_id_from_message(db: Session, user_message: str) -> int | None:
    """
    Only check DB if user explicitly typed an id.
    """
    m = _ID_PATTERN.search(user_message)
    if not m:
        return None
    pid = int(m.group(1))
    exists = db.query(Product.id).filter(Product.id == pid).first()
    return pid if exists else None


@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session = db.query(ChatSession).filter(ChatSession.session_id == data.session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    user_message = data.message.strip()
    if not user_message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    # Store user message
    db.add(ChatHistory(session_id=data.session_id, role="user", message=user_message, created_at=datetime.utcnow()))
    db.commit()

    # Context (last 12)
    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == data.session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    conversation_context = [{"role": h.role, "content": h.message} for h in history][-12:]

    # human active => stop gemini
    flag = get_flag(db, data.session_id)
    if flag and flag.status == "active":
        msg = "Customer service is handling this chat now."
        store_assistant(db, data.session_id, msg)
        return build_response(db, data.session_id, user_message, msg, product_id=None)

    intent = detect_intent(user_message, conversation_context)

    # Only extract product_id if user typed #id (no extra DB work otherwise)
    matched_product_id = extract_product_id_from_message(db, user_message)

    # ✅ Conditional DB retrieval
    rr = retrieve_products_for_prompt(
        db,
        user_message=user_message,
        intent=intent,
        conversation_context=conversation_context,
        matched_product_id=matched_product_id,
    )
    products_data = products_to_gemini_payload(rr.products) if rr.used else []

    logger.info(
        "chat session=%s intent=%s db_lookup=%s reason=%s products=%d",
        data.session_id,
        intent,
        rr.used,
        rr.reason,
        len(rr.products),
    )

    try:
        ai_answer = gemini_product_answer(
            prompt=user_message,
            products=products_data,
            conversation_history=conversation_context,
        )
    except Exception as exc:
        logger.exception("Gemini error during chat.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate AI response.",
        ) from exc

    store_assistant(db, data.session_id, ai_answer)

    trim_chat_history(db, data.session_id, max_messages=50)
    trim_chat_sessions(db, max_sessions=20, keep_session_id=data.session_id)

    return build_response(db, data.session_id, user_message, ai_answer, product_id=matched_product_id)