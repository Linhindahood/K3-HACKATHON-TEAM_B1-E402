"""Tests for security preflight checks and prompt injection isolation."""
from __future__ import annotations

import pytest
from backend.rag import ingest, prompt


def test_validate_content_preflight_rejects_placeholder():
    documents = [
        {
            "source": "fake.txt",
            "text": "> [Hưng] điền nội dung thật ở đây.",
        }
    ]
    ingest.validate_content_preflight(documents)
    assert documents[0]["is_placeholder"] is True



def test_validate_content_preflight_passes_valid_text():
    documents = [
        {
            "source": "valid.txt",
            "text": "Nội quy thư viện áp dụng cho toàn bộ học viên.",
        }
    ]
    ingest.validate_content_preflight(documents)


def test_prompt_builds_xml_context_delimiters():
    passages = [
        {"source": "doc1.txt", "text": "Học viên cần mang thẻ sinh viên."},
    ]
    formatted = prompt.build_user_prompt("Quy định mang thẻ?", passages)
    assert "<context_passages>" in formatted
    assert "</context_passages>" in formatted
    assert '<passage id="S1" source="doc1.txt">' in formatted
    assert "Học viên cần mang thẻ sinh viên." in formatted
