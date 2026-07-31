"""Tests for direction query node parsing V2 (LLM-driven, no rule-based keywords)."""
from __future__ import annotations

import pytest

from backend.rag.directions import parse_direction_nodes


def test_parse_direction_nodes_extracts_explicit_origin_and_destination():
    origin, destination = parse_direction_nodes(
        "Từ Ký túc xá đến Thư viện đi thế nào?",
        search_query="từ ký túc xá đến thư viện đi thế nào",
    )
    assert "ký túc xá" in origin.casefold()
    assert "thư viện" in destination.casefold()


def test_parse_direction_nodes_defaults_to_main_gate_when_origin_missing():
    origin, destination = parse_direction_nodes(
        "toa A o dau",
        search_query="tòa A ở đâu",
    )
    assert "Cổng chính" in origin
    assert "tòa A ở đâu" in destination


@pytest.mark.parametrize(
    ("question", "search_query"),
    [
        (
            "từ tòa E tôi muốn tìm bể bơi",
            "từ tòa E tìm bể bơi",
        ),
        (
            "đi từ tòa E, bể bơi ở đâu",
            "vị trí bể bơi từ tòa E",
        ),
        (
            "Tôi xuất phát tại tòa E, hãy chỉ đường tới thư viện",
            "chỉ đường tới thư viện",
        ),
    ],
)
def test_parse_direction_nodes_preserves_explicit_origin_from_question(
    question,
    search_query,
):
    origin, _ = parse_direction_nodes(question, search_query=search_query)

    assert origin.casefold() == "tòa e"
