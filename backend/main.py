import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, SessionLocal
from models import Product, ChatSession, ChatHistory
from schemas import (
    CreateSessionResponse,
    ChatRequest,
    ChatResponse,
    ChatHistoryOut
)
from gemini_ai import gemini_product_answer


app = FastAPI()

# Create all tables
Base.metadata.create_all(bind=engine)


# ---------------------------
# Database Dependency
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------
# CORS
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    # allow_origins=["*"],   # update to your frontend URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# Create Chat Session (FIXED)
# ---------------------------
@app.post("/create_session", response_model=CreateSessionResponse)
def create_session(db: Session = Depends(get_db)):
    # Generate a unique session ID as string
    session_id = str(uuid.uuid4())
    
    # Create new session with the generated ID and timestamp
    new_session = ChatSession(
        session_id=session_id,
        created_at=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return CreateSessionResponse(session_id=new_session.session_id)  # Use session_id, not id


# ---------------------------
# Chat Endpoint (FIXED)
# ---------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, db: Session = Depends(get_db)):

    # Check if session exists - session_id is now string (UUID)
    session = db.query(ChatSession).filter(ChatSession.session_id == data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Invalid session_id")

    # Save user message
    user_msg = ChatHistory(
        session_id=data.session_id,  # This is now a string UUID
        role="user",
        message=data.message
    )
    db.add(user_msg)
    db.commit()

    # Fetch products from DB and convert to dict list
    products = (
        db.query(Product)
        .order_by(Product.id.asc())
        .limit(50)
        .all()
    )
    products_data = [
        {"name": p.name, "description": p.description or "", "price": p.price or ""}
        for p in products
    ]

    # Get AI response
    try:
        ai_answer = gemini_product_answer(data.message, products_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save AI response
    bot_msg = ChatHistory(
        session_id=data.session_id,  # This is now a string UUID
        role="assistant",
        message=ai_answer
    )
    db.add(bot_msg)
    db.commit()

    return ChatResponse(
        session_id=data.session_id,
        user_message=data.message,
        bot_message=ai_answer
    )


# ---------------------------
# Chat History (FIXED)
# ---------------------------
@app.get("/history/{session_id}", response_model=list[ChatHistoryOut])
def get_history(session_id: str, db: Session = Depends(get_db)):  # Changed to str
    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.id.asc())
        .all()
    )

    if not history:
        raise HTTPException(status_code=404, detail="No chat history found")

    return history