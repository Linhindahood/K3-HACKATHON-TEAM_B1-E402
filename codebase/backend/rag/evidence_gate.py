"""Minimal evidence decision used before calling the generator."""
from __future__ import annotations

import math

from backend import config


def has_sufficient_evidence(passages: list[dict]) -> bool:
    if not passages:
        return False
    top_passage = passages[0]
    score = top_passage.get("dense_score", top_passage.get("score"))
    if score is None:
        return False
    try:
        score = float(score)
    except (ValueError, TypeError):
        return False
    if not math.isfinite(score) or score < config.EVIDENCE_DENSE_THRESHOLD:
        return False

    # Multi-signal check: if dense score is borderline, require non-zero lexical agreement if present
    lexical_score = top_passage.get("lexical_score")
    if lexical_score is not None:
        try:
            lex_score = float(lexical_score)
            if (
                math.isfinite(lex_score)
                and score < (config.EVIDENCE_DENSE_THRESHOLD + 0.02)
                and lex_score <= 0.0
            ):
                return False
        except (ValueError, TypeError):
            pass

    return True

