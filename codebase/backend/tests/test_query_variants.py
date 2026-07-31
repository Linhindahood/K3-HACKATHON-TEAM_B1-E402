"""Tests for query variant generation in Phase 3."""
from __future__ import annotations

from backend.rag.query_variants import generate_query_variants


def test_generate_query_variants_produces_accentless_only_for_unaccented_inputs():
    unaccented_question = "cach dat phong thu vien"
    search_query = "hướng dẫn đặt phòng thư viện microsoft outlook"

    variants = generate_query_variants(unaccented_question, search_query=search_query)

    assert variants["original"] == "cach dat phong thu vien"
    assert variants["accentless"] == "cach dat phong thu vien"
    assert variants["enhanced"] == "hướng dẫn đặt phòng thư viện microsoft outlook"


def test_generate_query_variants_skips_accentless_for_accented_inputs():
    accented_question = "Giờ mở cửa thư viện"
    variants = generate_query_variants(accented_question)

    assert variants["original"] == "Giờ mở cửa thư viện"
    assert "accentless" not in variants
    assert "enhanced" not in variants

