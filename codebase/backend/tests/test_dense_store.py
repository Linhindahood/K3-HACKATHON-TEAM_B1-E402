"""Tests for the resident FAISS index and chunk metadata mapping."""
from __future__ import annotations

import numpy as np
import pytest

from backend.rag import dense_store


class FakeIndex:
    d = 2
    ntotal = 2

    def search(self, query: np.ndarray, top_k: int):
        assert query.shape == (1, 2)
        return (
            np.asarray([[0.91, 0.82]], dtype=np.float32),
            np.asarray([[1, 0]], dtype=np.int64),
        )


def _chunks() -> list[dict]:
    return [
        {
            "chunk_id": "hours",
            "source": "library.txt",
            "text": "Giờ mở cửa",
            "source_url": "https://example.com/hours",
        },
        {
            "chunk_id": "room-a102",
            "source": "library.txt",
            "text": "Phòng A102 có 8 chỗ",
            "source_url": "https://example.com/rooms",
        },
    ]


def test_dense_store_maps_faiss_ids_to_source_metadata():
    store = dense_store.DenseStore(index=FakeIndex(), chunks=tuple(_chunks()))

    passages = store.search(np.asarray([1.0, 0.0], dtype=np.float32), top_k=2)

    assert passages == [
        {
            "text": "Phòng A102 có 8 chỗ",
            "source": "library.txt#room-a102",
            "score": pytest.approx(0.91),
            "chunk_id": "room-a102",
            "source_url": "https://example.com/rooms",
        },
        {
            "text": "Giờ mở cửa",
            "source": "library.txt#hours",
            "score": pytest.approx(0.82),
            "chunk_id": "hours",
            "source_url": "https://example.com/hours",
        },
    ]


def test_dense_store_rejects_wrong_query_dimension():
    store = dense_store.DenseStore(index=FakeIndex(), chunks=tuple(_chunks()))

    with pytest.raises(ValueError, match="dimension"):
        store.search(np.asarray([1.0], dtype=np.float32), top_k=2)


def test_dense_store_loader_is_resident_after_first_load(monkeypatch):
    dense_store.get_dense_store.cache_clear()
    calls: list[str] = []
    monkeypatch.setattr(dense_store, "_load_chunks", lambda: _chunks())
    monkeypatch.setattr(
        dense_store,
        "load_embedding_artifacts",
        lambda chunks: (
            calls.append("load")
            or (
                np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
                FakeIndex(),
                {"chunk_count": 2},
            )
        ),
    )

    first = dense_store.get_dense_store()
    second = dense_store.get_dense_store()

    assert first is second
    assert calls == ["load"]
    dense_store.get_dense_store.cache_clear()
