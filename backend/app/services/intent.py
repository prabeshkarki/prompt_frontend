from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

_ID_PATTERN = re.compile(r"(?:^|\s)(?:#|id\s*[:#]?\s*|product\s+)(\d+)\b", re.IGNORECASE)

# English + Nepali-ish keywords
CS_TRIGGERS = (
    "customer service", "support", "agent", "human", "representative",
    "talk to customer service", "connect me to customer service",
    "talk to agent", "need support",
)

RECO_TRIGGERS = (
    "recommend", "suggest", "best", "option",
    "budget", "under", "within",
    "vitra", "bhitra", "vitrama", "bhitrama",
    "ramro", "kun", "kasto", "chahiyo", "chahinchha", "chahincha",
    "price", "cost",
)

CATEGORY_WORDS = {
    "mobile": ("mobile", "phone", "smartphone", "mob", "cell"),
    "laptop": ("laptop", "notebook"),
    "tablet": ("tablet",),
}

USECASE_WORDS = (
    "photo", "camera", "battery", "gaming", "study", "office",
    "video", "editing", "performance",
    "photography", "vlog", "content",
    "game", "pubg", "free fire",
)

GREETINGS = {
    "hi", "hello", "hey", "yo", "hlo", "hlw", "namaste",
    "good morning", "good afternoon", "good evening",
}

MODELISH_TOKEN = re.compile(r"(?=.*[a-zA-Z])(?=.*\d)[A-Za-z0-9\-]{3,}")  # e.g. a54, s23, iPhone14


class Intent(str, Enum):
    CUSTOMER_SERVICE = "customer_service"
    EXACT_PRODUCT = "exact_product"
    RECOMMENDATION = "recommendation"
    CLARIFICATION = "clarification"
    CHAT = "chat"


@dataclass(frozen=True)
class ParsedContext:
    budget: Optional[int] = None
    category: Optional[str] = None


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def parse_budget(text: str) -> Optional[int]:
    """
    Handles: '50k', 'Rs 50000', '50000 rs', 'rs. 45000'
    Tries hard not to treat 'iphone 14' as budget.
    """
    t = normalize(text)

    # 50k / 60k style
    m = re.search(r"\b(\d{2,3})\s*k\b", t)
    if m:
        return int(m.group(1)) * 1000

    # Rs 50000 / rs.50000 / 50000 rs
    # require rs/ru/npr nearby so we don't capture random 14/15
    m = re.search(r"\b(?:rs\.?|npr|रु)\s*(\d{4,7})\b", t)
    if m:
        return int(m.group(1))

    m = re.search(r"\b(\d{4,7})\s*(?:rs\.?|npr|रु)\b", t)
    if m:
        return int(m.group(1))

    # "50k vitra" is already covered; avoid plain numbers (too risky)
    return None


def extract_category(text: str) -> Optional[str]:
    t = normalize(text)
    for cat, words in CATEGORY_WORDS.items():
        if any(w in t for w in words):
            return cat
    return None


def user_requests_customer_service(text: str) -> bool:
    t = normalize(text)
    return any(k in t for k in CS_TRIGGERS)


def looks_like_exact_product(text: str) -> bool:
    """
    Exact product: mentions #id OR contains model-ish token (letters+digits)
    and is not phrased like a budget/recommendation request.
    """
    t = normalize(text)
    if _ID_PATTERN.search(text):
        return True

    if any(k in t for k in RECO_TRIGGERS):
        return False

    # if message contains a model-ish token, likely exact
    if MODELISH_TOKEN.search(text):
        return True

    return False


def detect_intent(text: str, history: list[dict[str, str]] | None = None) -> Intent:
    t = normalize(text)
    if not t:
        return Intent.CHAT

    if user_requests_customer_service(t):
        return Intent.CUSTOMER_SERVICE

    if t in GREETINGS:
        return Intent.CHAT

    if looks_like_exact_product(text):
        return Intent.EXACT_PRODUCT

    # Recommendation: budget/category/“best/ramro/suggest/recommend”
    if parse_budget(text) is not None:
        return Intent.RECOMMENDATION

    if extract_category(text) is not None and any(k in t for k in RECO_TRIGGERS):
        return Intent.RECOMMENDATION

    if any(k in t for k in RECO_TRIGGERS):
        return Intent.RECOMMENDATION

    # Clarification: short “photo ko lagi”, “battery ramro” etc.
    if any(k in t for k in USECASE_WORDS) and extract_category(text) is None and parse_budget(text) is None:
        return Intent.CLARIFICATION

    return Intent.CHAT


def infer_context_from_history(history: list[dict[str, str]]) -> ParsedContext:
    """
    Scan last user messages to infer last budget/category.
    """
    budget = None
    category = None

    # look backwards, user-only
    for msg in reversed(history[-12:]):
        if msg.get("role") != "user":
            continue
        content = msg.get("content", "")
        if budget is None:
            budget = parse_budget(content)
        if category is None:
            category = extract_category(content)
        if budget is not None and category is not None:
            break

    return ParsedContext(budget=budget, category=category)