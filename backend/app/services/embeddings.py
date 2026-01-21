# app/services/embeddings.py
from __future__ import annotations

import os
from functools import lru_cache

from fastembed import TextEmbedding

# Pick a model that matches your language needs.
# English-focused: BAAI/bge-small-en-v1.5
# Multilingual: intfloat/multilingual-e5-small (if available in your fastembed build)
LOCAL_EMBED_MODEL = os.getenv("LOCAL_EMBED_MODEL", "BAAI/bge-small-en-v1.5")


@lru_cache(maxsize=1)
def _embedder() -> TextEmbedding:
    return TextEmbedding(model_name=LOCAL_EMBED_MODEL)


def embed_text(text: str) -> list[float]:
    t = (text or "").strip()
    if not t:
        return []
    it = iter(_embedder().embed([t]))
    vec = next(it)
    return vec.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    clean = [(t or "").strip() for t in texts]
    clean = [t for t in clean if t]
    if not clean:
        return []
    return [v.tolist() for v in _embedder().embed(clean)]