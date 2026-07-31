"""Tests for thin online retrieval orchestration."""
from __future__ import annotations

import numpy as np

from backend.rag import retriever


class FakeDenseStore:
    def __init__(self) -> None:
        self.calls: list[tuple[np.ndarray, int]] = []

    def search(self, query_vector: np.ndarray, top_k: int) -> list[dict]:
        self.calls.append((query_vector, top_k))
        return [
            {
                "text": "matched",
                "source": "source#chunk",
                "score": 0.9,
                "chunk_id": "chunk",
            }
        ]


class FakeLexicalStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, top_k: int) -> list[dict]:
        self.calls.append((query, top_k))
        return [
            {
                "text": "matched",
                "source": "source#chunk",
                "score": 2.0,
                "chunk_id": "chunk",
            }
        ]


def test_retrieve_normalizes_once_and_fuses_both_stores(monkeypatch):
    dense_store = FakeDenseStore()
    lexical_store = FakeLexicalStore()
    embedded: list[str] = []
    monkeypatch.setattr(
        retriever,
        "embed_query",
        lambda question: embedded.append(question)
        or np.asarray([1.0, 0.0], dtype=np.float32),
    )
    monkeypatch.setattr(retriever, "get_dense_store", lambda: dense_store)
    monkeypatch.setattr(retriever, "get_lexical_store", lambda: lexical_store)

    result = retriever.retrieve("  phòng  A102 có bao nhiêu chỗ?  ", top_k=3)

    assert embedded == ["phòng A102 có bao nhiêu chỗ?"]
    assert result[0]["source"] == "source#chunk"
    assert result[0]["dense_score"] == 0.9
    assert result[0]["lexical_score"] == 2.0
    assert len(lexical_store.calls) == 1
    assert lexical_store.calls[0] == ("phòng A102 có bao nhiêu chỗ?", retriever.CANDIDATE_K)




def test_fast_reject_does_not_load_model_or_store(monkeypatch):
    monkeypatch.setattr(
        retriever,
        "embed_query",
        lambda question: (_ for _ in ()).throw(AssertionError("must not embed")),
    )
    monkeypatch.setattr(
        retriever,
        "get_dense_store",
        lambda: (_ for _ in ()).throw(AssertionError("must not load store")),
    )
    monkeypatch.setattr(
        retriever,
        "get_lexical_store",
        lambda: (_ for _ in ()).throw(AssertionError("must not load store")),
    )

    assert retriever.retrieve(" ...?! ") == []
    assert retriever.retrieve("", top_k=4) == []
    assert retriever.retrieve("valid", top_k=0) == []


def test_warm_up_loads_both_model_and_store(monkeypatch):
    calls: list[str] = []
    dense_store = FakeDenseStore()
    lexical_store = FakeLexicalStore()
    monkeypatch.setattr(
        retriever, "warm_up_embedding", lambda: calls.append("model")
    )
    monkeypatch.setattr(
        retriever,
        "get_dense_store",
        lambda: calls.append("dense") or dense_store,
    )
    monkeypatch.setattr(
        retriever,
        "get_lexical_store",
        lambda: calls.append("lexical") or lexical_store,
    )

    result = retriever.warm_up()

    assert calls == ["dense", "lexical", "model"]
    assert result["chunk_count"] == 0
    assert result["lexical_chunk_count"] == 0
