from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, engine, get_db
from app.logger import logger
from app.models import ChatHistory, ChatSession, Product, UserProductHistory
from app.schemas import (
    ChatHistoryOut,
    ChatRequest,
    ChatResponse,
    CreateSessionResponse,
    ProductBase,
    ProductOut,
)
from app.services.confidence import compute_confidence
from app.services.context_protocol import ModelContext, render_prompt
from app.services.embeddings import embed_text
from app.services.history import summarize_history_for_prompt, trim_chat_history, trim_chat_sessions
from app.services.gemini_llm import generate_text
from app.services.rag_store import ensure_collection, search as rag_search, upsert as rag_upsert

settings = get_settings()

app = FastAPI(title="Product Chatbot API")

if settings.dev_create_tables:
    Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:3000",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def product_payload(p: Product) -> dict[str, Any]:
    return {
        "name": p.name,
        "category": p.category,
        "brand": p.brand,
        "screen": p.screen,
        "processor": p.processor,
        "ram": p.ram,
        "storage": p.storage,
        "camera": p.camera,
        "price": p.price,
    }


def product_to_doc(payload: dict[str, Any]) -> str:
    parts = [
        f"name: {payload.get('name','')}",
        f"category: {payload.get('category','')}",
        f"brand: {payload.get('brand','')}",
        f"screen: {payload.get('screen','')}",
        f"processor: {payload.get('processor','')}",
        f"ram: {payload.get('ram','')}",
        f"storage: {payload.get('storage','')}",
        f"camera: {payload.get('camera','')}",
        f"price_rs: {payload.get('price','')}",
    ]
    return "\n".join(x for x in parts if not x.endswith(": "))



def index_product(p: Product) -> None:
    payload = product_payload(p)
    doc = product_to_doc(payload)
    vec = embed_text(doc)
    ensure_collection(vector_size=len(vec))
    rag_upsert(product_id=p.id, vector=vec, payload={"id": p.id, **payload})


def record_purchase_intent(
    db: Session,
    session_id: str,
    user_message: str,
    candidates: list[dict[str, Any]],
) -> None:
    text = (user_message or "").lower()
    trigger_words = ("buy", "purchase", "order", "book")
    if not any(w in text for w in trigger_words):
        return

    matched = None
    for p in candidates:
        name = str(p.get("name", "")).lower().strip()
        if name and name in text:
            matched = p
            break

    if not matched:
        return

    entry = UserProductHistory(
        session_id=session_id,
        product_id=int(matched["id"]),
        product_name=str(matched["name"]),
    )
    db.add(entry)
    db.commit()

def fallback_answer_from_products(retrieved_products: list[dict[str, Any]]) -> str:
    if not retrieved_products:
        return "No matching products found in the catalog."

    lines: list[str] = ["Top matches from catalog:"]
    for i, p in enumerate(retrieved_products[:3], start=1):
        lines.append(f"{i}) {p.get('name','')} — Rs {p.get('price','')} (id {p.get('id')})")

        specs = []
        for k in ("brand", "category", "processor", "ram", "storage", "screen", "camera"):
            v = p.get(k)
            if v not in (None, "", "null"):
                specs.append(f"{k}:{v}")
        if specs:
            lines.append("   " + ", ".join(specs))

    return "\n".join(lines)

@app.on_event("startup")
def _startup_backfill_vector_index() -> None:
    # optional best-effort: ensure collection exists (needs vector size)
    # avoid embedding at startup if Gemini is down; only create when products are added/updated
    logger.info("Startup complete")


@app.get("/products", response_model=List[ProductOut])
def list_products(
    limit: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[Product]:
    return db.query(Product).limit(limit).all()


@app.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def add_product(product: ProductBase, db: Session = Depends(get_db)) -> Product:
    db_product = Product(
        name=product.name.strip(),
        category=(product.category or None),
        brand=(product.brand or None),
        screen=(product.screen or None),
        processor=(product.processor or None),
        ram=(product.ram or None),
        storage=(product.storage or None),
        camera=(product.camera or None),
        price=product.price,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    try:
        index_product(db_product)
    except Exception:
        logger.exception("Vector index failed for product_id=%s", db_product.id)

    return db_product


@app.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    product: ProductBase,
    db: Session = Depends(get_db),
) -> Product:
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_product.name = product.name.strip()
    db_product.category = (product.category or None)
    db_product.brand = (product.brand or None)
    db_product.screen = (product.screen or None)
    db_product.processor = (product.processor or None)
    db_product.ram = (product.ram or None)
    db_product.storage = (product.storage or None)
    db_product.camera = (product.camera or None)
    db_product.price = product.price

    db.commit()
    db.refresh(db_product)

    try:
        index_product(db_product)
    except Exception:
        logger.exception("Vector reindex failed for product_id=%s", db_product.id)

    return db_product


@app.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> dict:
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(db_product)
    db.commit()
    return {"message": f"Product ID {product_id} deleted"}


@app.post("/create_session", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(db: Session = Depends(get_db)) -> CreateSessionResponse:
    session_id = str(uuid.uuid4())
    new_session = ChatSession(session_id=session_id, created_at=datetime.utcnow())
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return CreateSessionResponse(session_id=session_id)


@app.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session = db.query(ChatSession).filter(ChatSession.session_id == data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = data.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    db.add(
        ChatHistory(
            session_id=data.session_id,
            role="user",
            message=user_message,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()

    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == data.session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    convo_summary = summarize_history_for_prompt(history)

    # RAG retrieval
    q_vec = embed_text(user_message)
    retrieved = rag_search(q_vec, top_k=settings.rag_top_k)

    # filter low score
    retrieved = [r for r in retrieved if r.score >= settings.rag_min_score]
    retrieved_products: list[dict[str, Any]] = []
    retrieved_scores: list[float] = []
    for r in retrieved:
        retrieved_products.append({"id": r.product_id, **r.payload})
        retrieved_scores.append(r.score)

    conf = compute_confidence(retrieved_scores, coverage=0.0)

    ctx = ModelContext(
        session_id=data.session_id,
        user_message=user_message,
        conversation_summary=convo_summary,
        confidence=conf.confidence,
        retrieved_products=retrieved_products,
        retrieval_scores=retrieved_scores,
    )
    prompt = render_prompt(ctx)
    bot_message = generate_text(prompt)

    # fallback only if Gemini is unavailable (not because retrieval is empty)
    if bot_message.startswith("LLM unavailable"):
        bot_message = fallback_answer_from_products(retrieved_products)

    db.add(
        ChatHistory(
            session_id=data.session_id,
            role="assistant",
            message=bot_message,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()

    record_purchase_intent(db, data.session_id, user_message, retrieved_products)

    trim_chat_history(db, data.session_id, max_messages=30)
    trim_chat_sessions(db, max_sessions=100)

    return ChatResponse(
        session_id=data.session_id,
        user_message=user_message,
        bot_message=bot_message,
        confidence=conf.confidence,
        retrieved_product_ids=[p["id"] for p in retrieved_products],
        debug={
            "top_score": conf.top_score,
            "mean_top3": conf.mean_top3,
            "scores": retrieved_scores[:8],
        } if settings.sqlalchemy_echo else None,
    )


@app.get("/history/{session_id}", response_model=List[ChatHistoryOut])
def get_history(
    session_id: str = Path(..., description="Chat session UUID"),
    db: Session = Depends(get_db),
) -> List[ChatHistoryOut]:
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    if not history:
        raise HTTPException(status_code=404, detail="No chat history found")

    return [ChatHistoryOut.model_validate(msg) for msg in history]