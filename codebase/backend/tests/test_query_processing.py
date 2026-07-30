"""Tests for conservative Vietnamese query normalization."""
from __future__ import annotations

from backend.rag.query_processing import lexical_tokens, normalize_query


def test_dense_query_keeps_accents_and_normalizes_unicode_and_whitespace():
    decomposed = "pho\u0300ng   tự\n học"

    assert normalize_query(decomposed) == "phòng tự học"


def test_lexical_tokens_include_accented_and_accentless_forms():
    assert lexical_tokens("Phòng A102 ở đâu?") == [
        "phòng",
        "phong",
        "a102",
        "ở",
        "o",
        "đâu",
        "dau",
    ]
