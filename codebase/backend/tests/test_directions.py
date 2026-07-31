"""Tests for direction query node parsing and location detection V1."""
from __future__ import annotations

from backend.rag.directions import is_location_query, parse_direction_nodes


def test_is_location_query_detects_keywords():
    assert is_location_query("Thư viện ở đâu?") is True
    assert is_location_query("Chỉ đường cho tôi tới Canteen") is True
    assert is_location_query("Xem bản đồ VinUni") is True
    assert is_location_query("Nội quy khóa học là gì?") is False


def test_parse_direction_nodes_extracts_explicit_origin_and_destination():
    origin, destination, is_loc = parse_direction_nodes("Từ Ký túc xá đến Thư viện đi thế nào?")
    assert is_loc is True
    assert "Ký túc xá" in origin
    assert "Thư viện" in destination


def test_parse_direction_nodes_defaults_to_main_gate_when_origin_missing():
    origin, destination, is_loc = parse_direction_nodes("Đường tới thư viện")
    assert is_loc is True
    assert "Cổng chính" in origin
