"""Tests for grounded generation orchestration."""
from __future__ import annotations

from backend.rag import generator
from backend.rag.llm_provider import LLMProviderError
from backend.rag.prompt import INSUFFICIENT_CONTEXT_TOKEN


def _passages(dense_score: float = 0.9) -> list[dict]:
    return [
        {
            "text": "Phòng A102 có sức chứa 8 chỗ.",
            "source": "library.txt#room-a102",
            "score": 0.93,
            "dense_score": dense_score,
            "chunk_id": "room-a102",
            "source_url": "https://example.com/rooms",
        },
        {
            "text": "Có thể đặt phòng bằng Outlook.",
            "source": "library.txt#booking",
            "score": 0.82,
            "dense_score": 0.84,
            "chunk_id": "booking",
            "source_url": "https://example.com/rooms",
        },
    ]


def test_low_evidence_returns_fallback_without_calling_provider(monkeypatch):
    monkeypatch.setattr(
        generator,
        "generate_text",
        lambda *args: (_ for _ in ()).throw(AssertionError("must not call LLM")),
    )

    result = generator.generate("Phòng A102 ở đâu?", _passages(0.7))

    assert result == {
        "answer": generator.FALLBACK_ANSWER,
        "sources": [],
        "has_evidence": False,
    }


def test_grounded_answer_uses_whitelisted_sources_and_urls(monkeypatch):
    captured = {}

    def fake_generate(system_prompt: str, user_prompt: str) -> str:
        captured["system"] = system_prompt
        captured["user"] = user_prompt
        return "A102 có 8 chỗ. [S1] https://evil.example/x"

    monkeypatch.setattr(generator, "generate_text", fake_generate)

    result = generator.generate("A102 có bao nhiêu chỗ?", _passages())

    assert "A102 có sức chứa 8 chỗ." in captured["user"]
    assert "https://evil.example/x" not in result["answer"]
    assert result["answer"].count("https://example.com/rooms") == 1
    assert result["sources"] == ["library.txt#room-a102"]
    assert result["has_evidence"] is True


def test_model_can_decline_insufficient_context(monkeypatch):
    monkeypatch.setattr(
        generator,
        "generate_text",
        lambda *args: INSUFFICIENT_CONTEXT_TOKEN,
    )

    result = generator.generate("Câu hỏi mơ hồ", _passages())

    assert result["has_evidence"] is False
    assert result["sources"] == []


def test_provider_failure_is_distinct_from_missing_evidence(monkeypatch):
    monkeypatch.setattr(
        generator,
        "generate_text",
        lambda *args: (_ for _ in ()).throw(LLMProviderError("failed")),
    )

    result = generator.generate("A102 có bao nhiêu chỗ?", _passages())

    assert result["answer"] == generator.PROVIDER_FAILURE_ANSWER
    assert result["has_evidence"] is True
    assert result["sources"] == [
        "library.txt#room-a102",
        "library.txt#booking",
    ]
