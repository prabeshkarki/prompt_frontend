# app/services/product_search.py
from __future__ import annotations

import re
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Product

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

_STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "please", "plz",
    "i", "me", "my", "you", "your", "is", "are", "a", "an", "to", "in", "on", "of",
    "ramro", "best", "recommend", "suggest", "vitra", "bhitra", "under", "within", "budget",
}

def keyword_search(db: Session, text: str, limit: int = 60) -> list[Product]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text)]
    tokens = [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]
    tokens = sorted(set(tokens), key=len, reverse=True)[:6]
    if not tokens:
        return []

    conditions = []
    for tok in tokens:
        like = f"%{tok}%"
        conditions.extend([
            Product.name.ilike(like),
            Product.brand.ilike(like),
            Product.category.ilike(like),
        ])

    return db.query(Product).filter(or_(*conditions)).limit(limit).all()

def recommend_search(db: Session, category: Optional[str], budget: Optional[int], limit: int = 60) -> list[Product]:
    q = db.query(Product)

    # Strategy 1: category + budget
    if category:
        q1 = q.filter(Product.category.ilike(f"%{category}%"))
        if budget:
            q1 = q1.filter(Product.price <= float(budget))
        r1 = q1.order_by(Product.price.asc()).limit(limit).all()
        if r1:
            return r1

    # Strategy 2: budget only
    if budget:
        r2 = (
            q.filter(Product.price <= float(budget))
            .order_by(Product.price.desc())  # give best value near budget
            .limit(limit)
            .all()
        )
        if r2:
            return r2

    # Strategy 3: category only
    if category:
        r3 = (
            q.filter(Product.category.ilike(f"%{category}%"))
            .order_by(Product.price.asc())
            .limit(limit)
            .all()
        )
        if r3:
            return r3

    # Strategy 4: fallback: just give something to talk about
    return q.order_by(Product.price.asc()).limit(limit).all()