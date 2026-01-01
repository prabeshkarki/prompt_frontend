from app.api.routers.products import router as products_router
from app.api.routers.chat import router as chat_router
from app.api.routers.sessions import router as sessions_router
from app.api.routers.history import router as history_router
from app.api.routers.support import router as support_router

__all__ = ["products_router", "chat_router", "sessions_router", "history_router", "support_router"]