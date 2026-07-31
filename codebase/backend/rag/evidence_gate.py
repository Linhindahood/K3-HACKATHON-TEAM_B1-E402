"""Minimal evidence decision used before calling the generator."""
from __future__ import annotations

import math

from backend import config


def evaluate_evidence_signals(passages: list[dict]) -> dict:
    """Evaluate multi-signal evidence metrics (dense score, margin, lexical score, agreement)."""
    if not passages:
        return {
            "has_passages": False,
            "top_dense_score": 0.0,
            "dense_margin": 0.0,
            "top_lexical_score": 0.0,
            "agreement": False,
        }

    top_passage = passages[0]
    score = top_passage.get("dense_score", top_passage.get("score", 0.0))
    try:
        top_dense = float(score) if math.isfinite(float(score)) else 0.0
    except (ValueError, TypeError):
        top_dense = 0.0

    second_dense = 0.0
    if len(passages) > 1:
        s2 = passages[1].get("dense_score", passages[1].get("score", 0.0))
        try:
            second_dense = float(s2) if math.isfinite(float(s2)) else 0.0
        except (ValueError, TypeError):
            second_dense = 0.0

    dense_margin = max(0.0, top_dense - second_dense)

    lex_score_raw = top_passage.get("lexical_score", 0.0)
    try:
        top_lexical = float(lex_score_raw) if math.isfinite(float(lex_score_raw)) else 0.0
    except (ValueError, TypeError):
        top_lexical = 0.0

    agreement = top_dense >= config.EVIDENCE_DENSE_THRESHOLD and top_lexical > 0.0

    return {
        "has_passages": True,
        "top_dense_score": top_dense,
        "dense_margin": dense_margin,
        "top_lexical_score": top_lexical,
        "agreement": agreement,
    }


def has_sufficient_evidence(passages: list[dict]) -> bool:
    """Multi-signal evidence decision before calling the generator."""
    if not passages:
        return False

    signals = evaluate_evidence_signals(passages)
    if not signals["has_passages"]:
        return False

    top_dense = signals["top_dense_score"]
    if top_dense < config.EVIDENCE_DENSE_THRESHOLD:
        return False

    # Borderline dense score requires non-zero lexical score agreement
    if top_dense < (config.EVIDENCE_DENSE_THRESHOLD + 0.02) and signals["top_lexical_score"] <= 0.0:
        return False

    return True


