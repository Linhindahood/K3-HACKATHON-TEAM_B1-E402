"""Tests for the HTTP-to-RAG coordinator boundary."""
from __future__ import annotations

from backend.api import routes


def test_ask_route_returns_pipeline_contract(monkeypatch):
    expected = {
        "answer": "grounded answer",
        "sources": ["source#chunk"],
        "has_evidence": True,
        "intent": "general",
    }
    if hasattr(routes, "rag_pipeline"):
        monkeypatch.setattr(
            routes.rag_pipeline,
            "answer_question",
            lambda question: expected,
        )
    else:
        monkeypatch.setattr(
            routes.retriever,
            "retrieve",
            lambda question: [{"text": "dummy", "source": "source#chunk", "score": 0.9}],
        )
        monkeypatch.setattr(
            routes.generator,
            "generate",
            lambda question, passages: expected,
        )

    response = routes.ask(routes.AskRequest(question="câu hỏi Discord"))

    assert response.model_dump() == expected

