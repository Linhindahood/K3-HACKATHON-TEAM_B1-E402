"""Tests for machine-owned citation extraction and validation in Phase 4."""
from __future__ import annotations

from backend.rag.citation_validator import (
    extract_citation_markers,
    validate_and_sanitize_citations,
)


def test_extract_citation_markers_finds_valid_markers():
    text = "Phòng A102 có sức chứa 8 chỗ [S1] và thuộc khu A [S2]."
    markers = extract_citation_markers(text)
    assert markers == ["S1", "S2"]


def test_validate_citations_strips_orphaned_markers():
    passages = [
        {"text": "Text 1", "source": "noi_quy.md#p1"},
    ]
    raw_answer = "Phòng A102 có 8 chỗ [S1] và có TV [S99]."

    cleaned, valid_sources, is_valid = validate_and_sanitize_citations(raw_answer, passages)

    assert cleaned == "Phòng A102 có 8 chỗ [S1] và có TV."
    assert valid_sources == ["noi_quy.md#p1"]
    assert is_valid is True


def test_validate_citations_invalidates_response_if_all_citations_are_invalid():
    passages = [
        {"text": "Text 1", "source": "noi_quy.md#p1"},
    ]
    raw_answer = "Thông tin bịa đặt hoàn toàn [S99] và [S100]."

    cleaned, valid_sources, is_valid = validate_and_sanitize_citations(raw_answer, passages)

    assert is_valid is False
    assert valid_sources == []
