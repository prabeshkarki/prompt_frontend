import uuid
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, SessionLocal
from models import Product, ChatSession, ChatHistory
from schemas import (
    CreateSessionResponse, ChatRequest, ChatResponse,
    ChatHistoryOut, ProductOut, ProductBase
)
from gemini_ai import gemini_product_answer
from logger import logger

app = FastAPI()
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Product Endpoints
# ---------------------------
@app.get("/products", response_model=list[ProductOut])
def list_products(
    limit: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching products with limit={limit}")
    products = db.query(Product).limit(limit).all()
    logger.info(f"Returned {len(products)} products")
    return products

@app.post("/products", response_model=ProductOut)
def add_product(product: ProductBase, db: Session = Depends(get_db)):
    logger.info(f"Adding product: {product.name}")

    db_product = Product(
        name=product.name.strip(),
        description=(product.description or "").strip(),
        price=product.price
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    logger.info(f"Products added with ID={db_product.id}")
    return db_product

@app.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    product: ProductBase,
    db: Session = Depends(get_db)
):
    logger.info(f"Updating product ID={product_id}")

    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        logger.warning(f"Product not found: ID={product_id}")
        raise HTTPException(status_code=404, detail="Product not found")

    db_product.name = product.name.strip()
    db_product.description = (product.description or "").strip()
    db_product.price = product.price
    db.commit()
    db.refresh(db_product)

    logger.info(f"Product updated: ID={product_id}")
    return db_product

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    logger.info(f"Deleting product ID={product_id}")

    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        logger.warning(f"Product not found: ID={product_id}")
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(db_product)
    db.commit()

    logger.info(f"Product deleted: ID={product_id}")
    return {"message": f"Product ID {product_id} deleted successfully"}


# ---------------------------
# Chat Session
# ---------------------------
@app.post("/create_session", response_model=CreateSessionResponse)
def create_session(db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    logger.info(f"Creating chat session: {session_id}")

    new_session = ChatSession(session_id=session_id, created_at=datetime.utcnow())
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return CreateSessionResponse(session_id=session_id)

# ---------------------------
# Chat Endpoint
# ---------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, db: Session = Depends(get_db)):
    logger.info(f"Chat request for session_id={data.session_id}")

    # Verify session exists
    session = db.query(ChatSession).filter(ChatSession.session_id == data.session_id).first()
    if not session:
        logger.warning(f"Session not found: {data.session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    user_msg = ChatHistory(session_id=data.session_id, role="user", message=data.message.strip())
    db.add(user_msg)
    db.commit()
    logger.info(f"User message saved for session {data.session_id}")

    # Fetch conversation history
    history = db.query(ChatHistory).filter(ChatHistory.session_id == data.session_id).order_by(ChatHistory.id.asc()).all()
    # fromat conversation history for context 
    conversation_context = []
    for msg in history:
        if not msg.role or not msg.message:
            continue
        conversation_context.append({
            "role":msg.role,
            "message":msg.message
        })
    logger.info(f"Fetched {len(conversation_context)} previous messages for context")

    # Fetch products
    products = db.query(Product).order_by(Product.id.asc()).limit(50).all()
    logger.info(f"Fetched {len(products)} products for chat context")

    products_data = [{"name": p.name, "description": p.description or "", "price": p.price} for p in products]

    # AI response
    try:
        ai_answer = gemini_product_answer(data.message, products_data, conversation_context)
    except Exception as e:
        logger.error(f"Gemini error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    bot_msg = ChatHistory(session_id=data.session_id, role="assistant", message=ai_answer)
    db.add(bot_msg)
    db.commit()
    logger.info(f"AI response saved for session {data.session_id}")

    return ChatResponse(session_id=data.session_id, user_message=data.message.strip(), bot_message=ai_answer)

# ---------------------------
# Chat History
# ---------------------------
@app.get("/history/{session_id}", response_model=list[ChatHistoryOut])
def get_history(session_id: str = Path(...), db: Session = Depends(get_db)):
    logger.info(f"Fetching chat history for : {session_id}")
    # Validate UUID format
    try:
        uuid.UUID(session_id)
    except ValueError:
        logger.error(f"Invalid session_id format: {session_id}")
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    history = db.query(ChatHistory).filter(ChatHistory.session_id == session_id).order_by(ChatHistory.id.asc()).all()
    if not history:
        logger.warning(f"No chat history found for session {session_id}")
        raise HTTPException(status_code=404, detail="No chat history found")
    logger.info(f"Returned {len(history)} chat messages")
    return history
