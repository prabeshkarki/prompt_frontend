from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import Base, engine

from app import models as _models # noqa: F401 # pyright: ignore[reportUnusedImport]

from app.api.routers.products import router as products_router
from app.api.routers.sessions import router as sessions_router
from app.api.routers.chat import router as chat_router
from app.api.routers.history import router as history_router

from app.api.routers.support import router as support_router

app = FastAPI(title="Product Chatbot API")

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(sessions_router)
app.include_router(support_router)
app.include_router(chat_router)
app.include_router(history_router)