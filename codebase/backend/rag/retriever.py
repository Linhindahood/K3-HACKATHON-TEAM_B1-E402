"""Thin orchestration for online dense retrieval."""
from __future__ import annotations

from backend.rag.dense_store import get_dense_store
from backend.rag.embedding_model import embed_query
from backend.rag.embedding_model import warm_up as warm_up_embedding

TOP_K = 4


def _is_searchable(question: str) -> bool:
    return any(character.isalnum() for character in question)


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    cleaned = question.strip()
    if top_k <= 0 or not _is_searchable(cleaned):
        return []
    query_vector = embed_query(cleaned)
    return get_dense_store().search(query_vector, top_k)


def warm_up() -> dict:
    """Load and retain index/chunks/model before serving online queries."""
    store = get_dense_store()
    warm_up_embedding()
    return {"chunk_count": getattr(store, "chunk_count", 0)}
