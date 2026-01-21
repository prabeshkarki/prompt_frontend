# app/services/rag_store.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from app.config import get_settings
from app.logger import logger

settings = get_settings()
client = QdrantClient(url=settings.qdrant_url)


@dataclass(frozen=True)
class Retrieved:
    product_id: int
    score: float
    payload: dict[str, Any]


def _collection_exists() -> bool:
    try:
        cols = client.get_collections().collections
        return any(c.name == settings.qdrant_collection for c in cols)
    except Exception as e:
        logger.error("Qdrant unavailable during get_collections: %s", e)
        return False


def ensure_collection(vector_size: int) -> None:
    if vector_size <= 0:
        return
    try:
        if _collection_exists():
            return
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
        )
        logger.info("Created Qdrant collection %s (size=%d)", settings.qdrant_collection, vector_size)
    except (ResponseHandlingException, UnexpectedResponse, httpx.ConnectError, httpx.NetworkError) as e:
        logger.error("Qdrant unavailable during ensure_collection: %s", e)


def upsert(product_id: int, vector: list[float], payload: dict[str, Any]) -> None:
    try:
        ensure_collection(vector_size=len(vector))
        client.upsert(
            collection_name=settings.qdrant_collection,
            points=[qm.PointStruct(id=product_id, vector=vector, payload=payload)],
        )
    except (ResponseHandlingException, UnexpectedResponse, httpx.ConnectError, httpx.NetworkError) as e:
        logger.error("Qdrant unavailable during upsert(product_id=%s): %s", product_id, e)


def search(query_vector: list[float], top_k: int) -> list[Retrieved]:
    if not query_vector:
        return []

    try:
        # guarantee collection exists using the query vector dimension
        ensure_collection(vector_size=len(query_vector))

        res = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        out: list[Retrieved] = []
        for p in (res.points or []):
            out.append(
                Retrieved(
                    product_id=int(p.id),
                    score=float(p.score),
                    payload=dict(p.payload or {}),
                )
            )
        return out

    except UnexpectedResponse as e:
        # handle "collection doesn't exist" without crashing the API
        if "doesn't exist" in str(e) or "Not found: Collection" in str(e):
            logger.error("Qdrant collection missing; returning empty retrieval: %s", e)
            try:
                ensure_collection(vector_size=len(query_vector))
            except Exception:
                pass
            return []
        logger.error("Qdrant unexpected response: %s", e)
        return []

    except (ResponseHandlingException, httpx.ConnectError, httpx.NetworkError) as e:
        logger.error("Qdrant unavailable during search: %s", e)
        return []