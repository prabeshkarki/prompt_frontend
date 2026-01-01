from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Product
from app.services.intent import Intent, parse_budget, extract_category, infer_context_from_history
from app.services.product_search import recommend_search, keyword_search

# configurable cap for prompt safety (DB can be huge; Gemini context cannot)
DEFAULT_LIMIT = int(os.getenv("GEMINI_PRODUCTS_LIMIT", "200"))

_MODELISH = re.compile(r"(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9\-]{3,}")  # A54, S23, iPhone14...

# minimal "follow-up specs" words to treat as continuation of product shopping
_FOLLOWUP_HINTS = (
    "gaming", "camera", "photo", "battery", "performance", "ram", "storage",
    "processor", "display", "screen", "fast", "smooth",
)

def _norm(text: str) -> str:
    return " ".join(text.lower().strip().split())

def _looks_like_followup(text: str) -> bool:
    t = _norm(text)
    if not t:
        return False
    if any(h in t for h in _FOLLOWUP_HINTS):
        return True
    # very short follow-ups like "gaming", "camera", "battery" also count
    if len(t.split()) <= 3 and len(t) <= 25:
        return True
    return False

@dataclass(frozen=True)
class RetrievalResult:
    products: list[Product]
    used: bool
    reason: str
    budget: Optional[int] = None
    category: Optional[str] = None


def should_retrieve_products(
    *,
    user_message: str,
    intent: Intent,
    conversation_context: list[dict[str, str]],
) -> bool:
    """
    Only retrieve products when:
      - user is doing exact lookup, or
      - user is asking for recommendations, or
      - user is clarifying in an ongoing shopping conversation
    """
    if intent in (Intent.EXACT_PRODUCT, Intent.RECOMMENDATION):
        return True

    # Clarification: only retrieve if it looks like a follow-up AND we have shopping context
    if intent == Intent.CLARIFICATION:
        inferred = infer_context_from_history(conversation_context)
        has_context = bool(inferred.budget or inferred.category)
        return has_context or _looks_like_followup(user_message)

    return False


def retrieve_products_for_prompt(
    db: Session,
    *,
    user_message: str,
    intent: Intent,
    conversation_context: list[dict[str, str]],
    matched_product_id: int | None,
    limit: int = DEFAULT_LIMIT,
) -> RetrievalResult:
    """
    Returns products to send to Gemini.
    DB access happens ONLY here.
    """
    if not should_retrieve_products(user_message=user_message, intent=intent, conversation_context=conversation_context):
        return RetrievalResult(products=[], used=False, reason="skip: not product-related")

    # Exact lookup: prefer explicit #id, else keyword search
    if intent == Intent.EXACT_PRODUCT:
        if matched_product_id is not None:
            p = db.query(Product).filter(Product.id == matched_product_id).first()
            return RetrievalResult(
                products=[p] if p else [],
                used=True,
                reason="exact: id" if p else "exact: id_not_found",
            )

        # model-ish token usually means exact lookup; keyword_search is fine
        prods = keyword_search(db, user_message, limit=limit)
        return RetrievalResult(products=prods, used=True, reason="exact: keyword_search")

    # Recommendation / clarification: infer budget/category then recommend_search
    budget = parse_budget(user_message)
    category = extract_category(user_message)

    if budget is None or category is None:
        inferred = infer_context_from_history(conversation_context)
        budget = budget if budget is not None else inferred.budget
        category = category if category is not None else inferred.category

    prods = recommend_search(db, category=category, budget=budget, limit=limit)

    # fallback: if recommendation filters yielded nothing, try keyword_search
    if not prods:
        prods = keyword_search(db, user_message, limit=limit)
        return RetrievalResult(products=prods, used=True, reason="reco: fallback_keyword", budget=budget, category=category)

    return RetrievalResult(products=prods, used=True, reason="reco: recommend_search", budget=budget, category=category)


def products_to_gemini_payload(products: list[Product]) -> list[dict]:
    """
    Convert Product rows to dicts for Gemini prompt.
    IMPORTANT: excludes product id.
    """
    return [
        {
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
        for p in products
    ]