"""Minimal evidence decision used before calling the generator."""
from __future__ import annotations

import math

from backend import config


def has_sufficient_evidence(passages: list[dict]) -> bool:
    if not passages:
        return False
    score = passages[0].get("dense_score", passages[0].get("score"))
    if score is None:
        return False
    score = float(score)
    return math.isfinite(score) and score >= config.EVIDENCE_DENSE_THRESHOLD
