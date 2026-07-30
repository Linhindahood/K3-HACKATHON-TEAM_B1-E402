"""Public coordinator for the complete RAG request flow."""
from __future__ import annotations

from backend.rag.generator import generate
from backend.rag.retriever import retrieve
from backend.rag.retriever import warm_up as warm_up_retriever


def answer_question(question: str) -> dict:
    """Retrieve evidence, then return the grounded generator output."""
    passages = retrieve(question)
    return generate(question, passages)


def warm_up() -> dict:
    """Load and retain retrieval models and indexes before serving requests."""
    return warm_up_retriever()
