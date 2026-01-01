from __future__ import annotations

import re
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models import Product, UserProductHistory

_ID_PATTERN = re.compile(r"(?:^|\s)(?:#|id\s*[:#]?\s*|product\s+)(\d+)\b", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

# English + Nepali-ish purchase triggers
_PURCHASE_TRIGGERS = (
    "buy", "purchase", "order", "book", "checkout",
    "kinchu", "kinna", "order gar", "book gar", "lina", "chahinchha", "chahincha",
)

_STOPWORDS = {
    "the","and","for","with","this","that","please","plz",
    "i","me","my","you","your","is","are","a","an","to","in","on","of",
    "rs","npr","budget","price",
}

def _norm(text: str) -> str:
    return " ".join(text.lower().strip().split())

def _looks_like_purchase(text: str) -> bool:
    t = _norm(text)
    return any(w in t for w in _PURCHASE_TRIGGERS)

def _find_product_by_id(db: Session, text: str) -> Optional[Product]:
    m = _ID_PATTERN.search(text)
    if not m:
        return None
    pid = int(m.group(1))
    return db.query(Product).filter(Product.id == pid).first()

def _find_product_by_keywords(db: Session, text: str) -> Optional[Product]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text)]
    tokens = [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]
    tokens = sorted(set(tokens), key=len, reverse=True)[:6]
    if not tokens:
        return None

    # Search name/brand/category for any token; pick first match.
    conditions = []
    for tok in tokens:
        like = f"%{tok}%"
        conditions.extend([
            Product.name.ilike(like),
            Product.brand.ilike(like),
            Product.category.ilike(like),
        ])

    return db.query(Product).filter(or_(*conditions)).order_by(Product.id.asc()).first()

def save_user_product_history_if_purchase(db: Session, session_id: str, user_message: str) -> None:
    """
    DB-driven tracking:
    - only runs if message looks like a purchase intent
    - tries #id first, then keyword match in DB
    - writes to user_product_history
    """
    msg = user_message.strip()
    if not msg:
        return
    if not _looks_like_purchase(msg):
        return

    product = _find_product_by_id(db, msg) or _find_product_by_keywords(db, msg)
    if not product:
        logger.info("Purchase intent detected but no product matched: %s", user_message)
        return

    entry = UserProductHistory(
        session_id=session_id,
        product_id=product.id,
        product_name=product.name,
    )
    db.add(entry)
    db.commit()
    logger.info("Saved purchase tracking: session=%s product_id=%s", session_id, product.id)