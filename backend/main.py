# from __future__ import annotations

# import uuid
# from datetime import datetime
# from typing import List

# from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
# from fastapi.middleware.cors import CORSMiddleware
# from sqlalchemy.orm import Session

# from database import Base, engine, get_db
# from gemini_ai import gemini_product_answer
# from logger import logger
# from models import ChatHistory, ChatSession, Product, UserProductHistory
# from schemas import (
#     ChatHistoryOut,
#     ChatRequest,
#     ChatResponse,
#     CreateSessionResponse,
#     ProductBase,
#     ProductOut,
# )

# app = FastAPI(title="Product Chatbot API")

# # Simple dev-time table creation
# Base.metadata.create_all(bind=engine)


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# def user_product_history(
#     db: Session,
#     session_id: str,
#     user_message: str,
#     products: List
# ) -> None:
#     """
#     Save product_id, session_id, and product_name into user_product_history
#     if the user message indicates a purchase and matches a product name.
#     """
#     text = user_message.lower()

#     # very simple intent check
#     trigger_words = ("buy", "purchase", "order", "book")
#     if not any(w in text for w in trigger_words):
#         return

#     # naive product matching: check if product name appears in the message
#     matched_product: Product | None = None
#     for p in products:
#         if p.name.lower() in text:
#             matched_product = p
#             break

#     if not matched_product:
#         logger.info(
#             "Purchase-like message but no product name matched: %s", user_message
#         )
#         return

#     entry = UserProductHistory(
#         session_id=session_id,
#         product_id=matched_product.id,
#         product_name=matched_product.name,
#     )
#     db.add(entry)
#     db.commit()
#     logger.info(
#         "Saved user_product_history for session %s and product %s",
#         session_id,
#         matched_product.name,
#     )

# def trim_chat_history(db: Session, session_id: str, max_messages: int = 20) -> None:
#     """
#     Keep only the latest `max_messages` messages for a given session_id.
#     Delete older ones from the database.
#     """
#     messages = (
#         db.query(ChatHistory)
#         .filter(ChatHistory.session_id == session_id)
#         .order_by(ChatHistory.created_at.desc())  # newest first
#         .all()
#     )

#     if len(messages) <= max_messages:
#         return

#     # Messages after index `max_messages` are old and should be deleted
#     to_delete = messages[max_messages:]
#     for msg in to_delete:
#         db.delete(msg)
#     db.commit()
#     logger.info(
#         "Trimmed chat history for session %s: deleted %d old messages",
#         session_id,
#         len(to_delete),
#     )

# def trim_chat_sessions(db: Session, max_sessions: int = 20) -> None:
#     """
#     Keep only the latest `max_sessions` ChatSession rows (by created_at).
#     Older sessions (and their histories, via cascade) will be deleted.
#     """
#     sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()

#     if len(sessions) <= max_sessions:
#         return

#     to_delete = sessions[max_sessions:]  # older sessions
#     for s in to_delete:
#         db.delete(s)
#     db.commit()
#     logger.info(
#         "Trimmed chat sessions: deleted %d old sessions",
#         len(to_delete),
#     )

# @app.get("/products", response_model=List[ProductOut])
# def list_products(
#     limit: int = Query(10, ge=1, le=500),
#     db: Session = Depends(get_db),
# ) -> List[Product]:
#     logger.info("Fetching products with limit=%s", limit)
#     products = db.query(Product).limit(limit).all()
#     logger.info("Returned %d products", len(products))
#     return products


# @app.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
# def add_product(product: ProductBase, db: Session = Depends(get_db)) -> Product:
#     logger.info("Adding product: %s", product.name)

#     db_product = Product(
#         name=product.name.strip(),
#         # description=(product.description or "").strip(),
#         category=(product.category or None),
#         brand=(product.brand or None),
#         screen=(product.screen or None),
#         processor=(product.processor or None),
#         ram=(product.ram or None),
#         storage=(product.storage or None),
#         camera=(product.camera or None),
#         price=product.price,
#     )
#     db.add(db_product)
#     db.commit()
#     db.refresh(db_product)

#     logger.info("Product added with ID=%s", db_product.id)
#     return db_product


# @app.put("/products/{product_id}", response_model=ProductOut)
# def update_product(
#     product_id: int,
#     product: ProductBase,
#     db: Session = Depends(get_db),
# ) -> Product:
#     logger.info("Updating product ID=%s", product_id)

#     db_product = db.query(Product).filter(Product.id == product_id).first()
#     if not db_product:
#         logger.warning("Product not found: ID=%s", product_id)
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Product not found",
#         )

#     db_product.name = product.name.strip()
#     # db_product.description = (product.description or "").strip()
#     db_product.category = (product.category or None)
#     db_product.brand = (product.brand or None)
#     db_product.screen = (product.screen or None)
#     db_product.processor = (product.processor or None)
#     db_product.ram = (product.ram or None)
#     db_product.storage = (product.storage or None)
#     db_product.camera = (product.camera or None)
#     db_product.price = product.price

#     db.commit()
#     db.refresh(db_product)

#     logger.info("Product updated: ID=%s", product_id)
#     return db_product


# @app.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
# def delete_product(
#     product_id: int,
#     db: Session = Depends(get_db),
# ) -> dict:
#     logger.info("Deleting product ID=%s", product_id)

#     db_product = db.query(Product).filter(Product.id == product_id).first()
#     if not db_product:
#         logger.warning("Product not found: ID=%s", product_id)
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Product not found",
#         )

#     db.delete(db_product)
#     db.commit()

#     logger.info("Product deleted: ID=%s", product_id)
#     return {"message": f"Product ID {product_id} deleted successfully"}


# @app.post(
#     "/create_session",
#     response_model=CreateSessionResponse,
#     status_code=status.HTTP_201_CREATED,
# )
# def create_session(db: Session = Depends(get_db)) -> CreateSessionResponse:
#     """Create a new chat session and return its UUID."""
#     session_id = str(uuid.uuid4())
#     logger.info("Creating chat session: %s", session_id)

#     new_session = ChatSession(session_id=session_id, created_at=datetime.utcnow())
#     db.add(new_session)
#     db.commit()
#     db.refresh(new_session)

#     return CreateSessionResponse(session_id=session_id)


# @app.post("/chat", response_model=ChatResponse)
# def chat(data: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
#     logger.info("Chat request for session_id=%s", data.session_id)

#     # Ensure the session exists
#     session = (
#         db.query(ChatSession)
#         .filter(ChatSession.session_id == data.session_id)
#         .first()
#     )
#     if not session:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Session not found",
#         )

#     user_message = data.message.strip()
#     if not user_message:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Message cannot be empty",
#         )

#     # Store user message
#     user_entry = ChatHistory(
#         session_id=data.session_id,
#         role="user",
#         message=user_message,
#         created_at=datetime.utcnow(),
#     )
#     db.add(user_entry)
#     db.commit()

#     # Fetch conversation history ordered by time
#     history = (
#         db.query(ChatHistory)
#         .filter(ChatHistory.session_id == data.session_id)
#         .order_by(ChatHistory.created_at.asc())
#         .all()
#     )

#     # Convert to simple role/content format for Gemini helper
#     conversation_context: list[dict[str, str]] = [
#         {"role": msg.role, "content": msg.message} for msg in history
#     ]

#     # Keep only the last N messages to avoid huge prompts
#     max_messages = 12
#     if len(conversation_context) > max_messages:
#         conversation_context = conversation_context[-max_messages:]

#     # Load a subset of products for context
#     products = db.query(Product).limit(300).all()
#     products_data = [
#         {
#             "name": p.name,
#             "category": p.category,
#             "brand": p.brand,
#             "screen": p.screen,
#             "processor": p.processor,
#             "ram": p.ram,
#             "storage": p.storage,
#             "camera": p.camera,
#             "price": p.price,
#         }
#         for p in products
#     ]

#     # Call Gemini
#     try:
#         ai_answer = gemini_product_answer(
#             prompt=user_message,
#             products=products_data,
#             conversation_history=conversation_context,
#         )
#     except Exception as exc:
#         logger.exception("Gemini error during chat.")
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail="Failed to generate AI response.",
#         ) from exc

#     # Store assistant reply
#     bot_entry = ChatHistory(
#         session_id=data.session_id,
#         role="assistant",
#         message=ai_answer,
#         created_at=datetime.utcnow(),
#     )
#     db.add(bot_entry)
#     db.commit()

#     trim_chat_history(db, data.session_id, max_messages=20)
#     trim_chat_sessions(db, max_sessions=50)

#     return ChatResponse(
#         session_id=data.session_id,
#         user_message=user_message,
#         bot_message=ai_answer,
#     )

# @app.get("/history/{session_id}", response_model=List[ChatHistoryOut])
# def get_history(
#     session_id: str = Path(..., description="Chat session UUID"),
#     db: Session = Depends(get_db),
# ) -> List[ChatHistoryOut]:
#     logger.info("Fetching chat history for session %s", session_id)

#     # Validate UUID format
#     try:
#         uuid.UUID(session_id)
#     except ValueError:
#         logger.error("Invalid session_id format: %s", session_id)
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid session_id format",
#         )

#     # Ensure session exists
#     session = (
#         db.query(ChatSession)
#         .filter(ChatSession.session_id == session_id)
#         .first()
#     )
#     if not session:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Session not found",
#         )

#     history = (
#         db.query(ChatHistory)
#         .filter(ChatHistory.session_id == session_id)
#         .order_by(ChatHistory.created_at.asc())
#         .all()
#     )

#     if not history:
#         logger.warning("No chat history found for session %s", session_id)
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="No chat history found",
#         )

#     logger.info("Returned %d chat messages", len(history))
#     return [ChatHistoryOut.from_orm(msg) for msg in history]


# # @app.delete("/session/{session_id}", status_code=status.HTTP_200_OK)
# # def delete_session(
# #     session_id: str = Path(..., description="Chat session UUID"),
# #     db: Session = Depends(get_db),
# # ) -> dict:
# #     logger.info("Deleting chat session %s", session_id)

# #     # Validate UUID format
# #     try:
# #         uuid.UUID(session_id)
# #     except ValueError:
# #         logger.error("Invalid session_id format: %s", session_id)
# #         raise HTTPException(
# #             status_code=status.HTTP_400_BAD_REQUEST,
# #             detail="Invalid session_id format",
# #         )

# #     # Find session
# #     session = (
# #         db.query(ChatSession)
# #         .filter(ChatSession.session_id == session_id)
# #         .first()
# #     )
# #     if not session:
# #         logger.warning("Session not found: %s", session_id)
# #         raise HTTPException(
# #             status_code=status.HTTP_404_NOT_FOUND,
# #             detail="Session not found",
# #         )

# #     # Deleting ChatSession will also delete ChatHistory because of cascade
# #     db.delete(session)
# #     db.commit()

# #     logger.info("Session deleted: %s", session_id)
# #     return {"message": f"Session {session_id} deleted successfully"}

