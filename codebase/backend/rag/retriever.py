"""Thin orchestration for online hybrid retrieval."""
from __future__ import annotations

from backend.rag.dense_store import get_dense_store
from backend.rag.embedding_model import embed_query
from backend.rag.embedding_model import warm_up as warm_up_embedding
from backend.rag.fusion import fuse_results
from backend.rag.lexical_store import get_lexical_store
from backend.rag.query_processing import normalize_query

from backend.rag.query_variants import generate_query_variants

TOP_K = 4
CANDIDATE_K = 8
DENSE_WEIGHT = 0.7


def _is_searchable(question: str) -> bool:
    return any(character.isalnum() for character in question)


def retrieve(
    question: str,
    top_k: int = TOP_K,
    search_query: str | None = None,
) -> list[dict]:
    cleaned = normalize_query(question)
    if top_k <= 0 or not _is_searchable(cleaned):
        return []

    candidate_k = max(top_k, CANDIDATE_K)
    variants = generate_query_variants(cleaned, search_query=search_query)

    # Dense Search on original query (Multilingual E5 ONNX)
    query_vector = embed_query(variants["original"])
    dense_results = get_dense_store().search(query_vector, candidate_k)

    # Multi-variant Lexical Search (BM25S)
    lexical_store = get_lexical_store()
    lexical_results = []
    seen_chunks = set()
    for variant_query in variants.values():
        results = lexical_store.search(variant_query, candidate_k)
        for item in results:
            chunk_id = item.get("chunk_id")
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                lexical_results.append(item)

    return fuse_results(
        dense_results,
        lexical_results,
        top_k=top_k,
        dense_weight=DENSE_WEIGHT,
    )



def warm_up() -> dict:
    """Load and retain both indexes and the model before serving queries."""
    dense_store = get_dense_store()
    lexical_store = get_lexical_store()
    warm_up_embedding()
    return {
        "chunk_count": getattr(dense_store, "chunk_count", 0),
        "lexical_chunk_count": getattr(lexical_store, "chunk_count", 0),
    }
