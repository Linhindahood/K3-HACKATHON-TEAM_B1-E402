"""Tests for multi-signal evidence gate safety decisions."""
from __future__ import annotations

import math
from backend import config
from backend.rag.evidence_gate import has_sufficient_evidence


def test_empty_passages_returns_false():
    assert has_sufficient_evidence([]) is False


def test_missing_or_invalid_score_returns_false():
    assert has_sufficient_evidence([{"text": "foo"}]) is False
    assert has_sufficient_evidence([{"text": "foo", "dense_score": None}]) is False
    assert has_sufficient_evidence([{"text": "foo", "dense_score": "invalid"}]) is False
    assert has_sufficient_evidence([{"text": "foo", "dense_score": math.nan}]) is False
    assert has_sufficient_evidence([{"text": "foo", "dense_score": math.inf}]) is False


def test_dense_score_below_threshold_returns_false():
    low_score = config.EVIDENCE_DENSE_THRESHOLD - 0.05
    assert has_sufficient_evidence([{"text": "foo", "dense_score": low_score}]) is False


def test_valid_dense_score_returns_true():
    high_score = config.EVIDENCE_DENSE_THRESHOLD + 0.05
    assert has_sufficient_evidence([{"text": "foo", "dense_score": high_score}]) is True


def test_borderline_dense_score_with_zero_lexical_returns_false():
    borderline = config.EVIDENCE_DENSE_THRESHOLD + 0.01
    passage = {
        "text": "foo",
        "dense_score": borderline,
        "lexical_score": 0.0,
    }
    assert has_sufficient_evidence([passage]) is False


def test_evaluate_evidence_signals_computes_margin_and_agreement():
    from backend.rag.evidence_gate import evaluate_evidence_signals

    passages = [
        {"text": "p1", "dense_score": 0.9, "lexical_score": 2.5},
        {"text": "p2", "dense_score": 0.7, "lexical_score": 1.0},
    ]
    signals = evaluate_evidence_signals(passages)
    assert signals["has_passages"] is True
    assert signals["top_dense_score"] == 0.9
    assert abs(signals["dense_margin"] - 0.2) < 1e-5
    assert signals["top_lexical_score"] == 2.5
    assert signals["agreement"] is True


