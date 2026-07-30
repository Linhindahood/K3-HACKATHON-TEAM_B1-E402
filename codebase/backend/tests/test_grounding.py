"""Tests for deterministic passage, citation, and URL handling."""
from __future__ import annotations

from backend.rag import grounding


def test_selection_removes_invalid_and_duplicate_sources(monkeypatch):
    monkeypatch.setattr(grounding.config, "GENERATOR_MAX_PASSAGES", 2)
    passages = [
        {"source": "a#1", "text": "one"},
        {"source": "a#1", "text": "duplicate"},
        {"source": "", "text": "invalid"},
        {"source": "b#2", "text": "two"},
        {"source": "c#3", "text": "three"},
    ]

    selected = grounding.select_passages(passages)

    assert [passage["source"] for passage in selected] == ["a#1", "b#2"]


def test_url_sanitizer_only_keeps_retrieved_whitelist():
    passages = [
        {
            "source": "library#hours",
            "text": "hours",
            "source_url": "https://example.com/hours",
        }
    ]
    answer = (
        "Đúng: https://example.com/hours. "
        "Sai: https://evil.example/path."
    )

    sanitized = grounding.sanitize_urls(answer, passages)

    assert "https://example.com/hours" in sanitized
    assert "https://evil.example/path" not in sanitized


def test_sources_deduplicate_shared_url():
    passages = [
        {
            "source": "library#a102",
            "text": "A102",
            "source_url": "https://example.com/rooms",
        },
        {
            "source": "library#a103",
            "text": "A103",
            "source_url": "https://example.com/rooms",
        },
    ]

    answer = grounding.attach_sources("Nội dung", passages)

    assert answer.count("https://example.com/rooms") == 1
    assert "library#a102" in answer
    assert "library#a103" in answer


def test_citations_select_only_whitelisted_passages():
    passages = [
        {"source": "library#a102", "text": "A102"},
        {"source": "library#booking", "text": "Booking"},
    ]

    cited = grounding.cited_passages("Tám chỗ [S1]. Bỏ qua [S9].", passages)
    sanitized = grounding.sanitize_citations(
        "Tám chỗ [S1]. Bỏ qua [S9].",
        len(passages),
    )

    assert [passage["source"] for passage in cited] == ["library#a102"]
    assert sanitized == "Tám chỗ [S1]. Bỏ qua ."
