"""Deterministic weighted fusion for dense and lexical candidates."""
from __future__ import annotations

import math


def fuse_results(
    dense_results: list[dict],
    lexical_results: list[dict],
    top_k: int,
    dense_weight: float,
) -> list[dict]:
    if top_k <= 0:
        return []
    if not 0.0 <= dense_weight <= 1.0:
        raise ValueError("dense_weight must be between 0 and 1")

    lexical_max = max(
        (result["score"] for result in lexical_results),
        default=0.0,
    )
    candidates: dict[str, dict] = {}

    for result in dense_results:
        key = result.get("chunk_id", result["source"])
        score = float(result["score"])
        if not math.isfinite(score):
            continue
        candidate = candidates.setdefault(
            key,
            {"passage": result, "dense_score": None, "lexical_score": None},
        )
        candidate["dense_score"] = score

    for result in lexical_results:
        key = result.get("chunk_id", result["source"])
        score = float(result["score"])
        if not math.isfinite(score) or score <= 0:
            continue
        candidate = candidates.setdefault(
            key,
            {"passage": result, "dense_score": None, "lexical_score": None},
        )
        candidate["lexical_score"] = score

    fused = []
    for candidate in candidates.values():
        dense_score = candidate["dense_score"]
        lexical_score = candidate["lexical_score"]
        normalized_dense = (
            min(max(dense_score, 0.0), 1.0) if dense_score is not None else 0.0
        )
        normalized_lexical = (
            lexical_score / lexical_max
            if lexical_score is not None and lexical_max > 0
            else 0.0
        )
        passage = dict(candidate["passage"])
        passage["score"] = (
            dense_weight * normalized_dense
            + (1.0 - dense_weight) * normalized_lexical
        )
        passage["dense_score"] = dense_score
        passage["lexical_score"] = lexical_score
        fused.append(passage)

    fused.sort(
        key=lambda passage: (
            -passage["score"],
            passage.get("chunk_id", passage["source"]),
        )
    )
    return fused[:top_k]
