"""Tests for minimal weighted dense/BM25 fusion."""
from __future__ import annotations

import pytest

from backend.rag.fusion import fuse_results


def _passage(chunk_id: str, score: float) -> dict:
    return {
        "chunk_id": chunk_id,
        "source": f"source#{chunk_id}",
        "text": chunk_id,
        "score": score,
    }


def test_fusion_combines_scores_and_deduplicates_chunks():
    results = fuse_results(
        dense_results=[_passage("semantic", 0.9), _passage("exact", 0.8)],
        lexical_results=[_passage("exact", 4.0)],
        top_k=2,
        dense_weight=0.7,
    )

    assert [result["chunk_id"] for result in results] == ["exact", "semantic"]
    assert results[0]["score"] == pytest.approx(0.86)
    assert results[0]["dense_score"] == 0.8
    assert results[0]["lexical_score"] == 4.0
    assert len(results) == 2


def test_fusion_rejects_invalid_weight():
    with pytest.raises(ValueError, match="dense_weight"):
        fuse_results([], [], top_k=4, dense_weight=1.1)
