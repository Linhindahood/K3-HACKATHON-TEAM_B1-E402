"""Tests for the public RAG coordinator."""
from __future__ import annotations

from backend.rag import pipeline


def test_answer_question_coordinates_retrieval_then_generation(monkeypatch):
    calls = []
    passages = [{"text": "evidence", "source": "source#chunk", "score": 0.9}]
    expected = {
        "answer": "grounded answer",
        "sources": ["source#chunk"],
        "has_evidence": True,
    }
    monkeypatch.setattr(
        pipeline,
        "retrieve",
        lambda question: calls.append(("retrieve", question)) or passages,
    )
    monkeypatch.setattr(
        pipeline,
        "generate",
        lambda question, evidence: calls.append(
            ("generate", question, evidence)
        )
        or expected,
    )

    result = pipeline.answer_question("câu hỏi")

    assert result is expected
    assert calls == [
        ("retrieve", "câu hỏi"),
        ("generate", "câu hỏi", passages),
    ]


def test_pipeline_warm_up_delegates_to_retriever(monkeypatch):
    expected = {"chunk_count": 89, "lexical_chunk_count": 89}
    monkeypatch.setattr(pipeline, "warm_up_retriever", lambda: expected)

    assert pipeline.warm_up() is expected
