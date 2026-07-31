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
    monkeypatch.setattr(pipeline, "route_query", lambda q: (pipeline.Intent.FACTUAL, q, False))
    monkeypatch.setattr(
        pipeline,
        "retrieve",
        lambda question, search_query=None: calls.append(("retrieve", question)) or passages,
    )


    monkeypatch.setattr(
        pipeline,
        "generate",
        lambda question, evidence: calls.append(
            ("generate", question, evidence)
        )
        or expected,
    )

    result = pipeline.answer_question("Nội quy là gì?")

    assert result["answer"] == expected["answer"]
    assert result["intent"] == "factual"
    assert calls == [
        ("retrieve", "Nội quy là gì?"),
        ("generate", "Nội quy là gì?", passages),
    ]


def test_answer_question_fast_path_for_greeting(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "retrieve",
        lambda question: (_ for _ in ()).throw(AssertionError("Must not retrieve")),
    )
    monkeypatch.setattr(
        pipeline,
        "generate",
        lambda question, evidence: (_ for _ in ()).throw(AssertionError("Must not generate")),
    )

    result = pipeline.answer_question("chào bạn")

    assert result["has_evidence"] is False
    assert result["sources"] == []
    assert result["intent"] == "greeting"
    assert "Chào bạn" in result["answer"]



def test_pipeline_warm_up_delegates_to_retriever(monkeypatch):
    expected = {"chunk_count": 89, "lexical_chunk_count": 89}
    monkeypatch.setattr(pipeline, "warm_up_retriever", lambda: expected)

    assert pipeline.warm_up() is expected
