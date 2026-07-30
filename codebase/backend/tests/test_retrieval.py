"""Tests for thin online retrieval orchestration."""
from __future__ import annotations

import numpy as np

from backend.rag import retriever


class FakeStore:
    def __init__(self) -> None:
        self.calls: list[tuple[np.ndarray, int]] = []

    def search(self, query_vector: np.ndarray, top_k: int) -> list[dict]:
        self.calls.append((query_vector, top_k))
        return [{"text": "matched", "source": "source#chunk", "score": 0.9}]


def test_retrieve_embeds_once_and_delegates_to_dense_store(monkeypatch):
    store = FakeStore()
    embedded: list[str] = []
    monkeypatch.setattr(
        retriever,
        "embed_query",
        lambda question: embedded.append(question)
        or np.asarray([1.0, 0.0], dtype=np.float32),
    )
    monkeypatch.setattr(retriever, "get_dense_store", lambda: store)

    result = retriever.retrieve("  phòng A102 có bao nhiêu chỗ?  ", top_k=3)

    assert embedded == ["phòng A102 có bao nhiêu chỗ?"]
    assert result[0]["source"] == "source#chunk"
    assert store.calls[0][1] == 3


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

    assert retriever.retrieve(" ...?! ") == []
    assert retriever.retrieve("", top_k=4) == []
    assert retriever.retrieve("valid", top_k=0) == []


def test_warm_up_loads_both_model_and_store(monkeypatch):
    calls: list[str] = []
    store = FakeStore()
    monkeypatch.setattr(
        retriever, "warm_up_embedding", lambda: calls.append("model")
    )
    monkeypatch.setattr(
        retriever,
        "get_dense_store",
        lambda: calls.append("store") or store,
    )

    result = retriever.warm_up()

    assert calls == ["store", "model"]
    assert result["chunk_count"] == 0
