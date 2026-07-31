"""Tests for retrieval robustness on accentless, typo, abbreviation, and English queries."""
from __future__ import annotations

import pytest
from backend.rag.retriever import retrieve


def test_retrieval_handles_accentless_queries():
    results = retrieve("cach dat phong thu vien", top_k=3)
    assert len(results) > 0
    assert any(
        "2_Handbook_AI_IN_ACTION.txt" in res["source"]
        or "4_gio_mo_cua_library.txt" in res["source"]
        for res in results
    )




def test_retrieval_handles_english_queries():
    results = retrieve("where is the library located", top_k=3)
    assert len(results) > 0
    assert any("4_gio_mo_cua_library.txt" in res["source"] or "1_map.png" in res["source"] for res in results)


def test_retrieval_handles_enhanced_search_query():
    results = retrieve(
        "Chào bạn, phg A102 chứa được mấy người",
        top_k=3,
        search_query="phòng A102 sức chứa số chỗ",
    )
    assert len(results) > 0
    assert any("A102" in res["text"] for res in results)


def test_retrieval_prioritizes_outlook_booking_instructions():
    results = retrieve(
        "Cách đặt phòng trong thư viện như thế nào?",
        top_k=3,
        search_query="hướng dẫn đặt phòng thư viện bằng Microsoft Outlook",
    )

    assert results[0]["chunk_id"] == "huong-dan-dat-phong-bang-microsoft-outlook"
