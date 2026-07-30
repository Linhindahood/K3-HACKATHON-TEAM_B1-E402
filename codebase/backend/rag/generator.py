"""Thin orchestration for grounded answer generation."""
from __future__ import annotations

from backend.rag.evidence_gate import has_sufficient_evidence
from backend.rag.grounding import (
    attach_sources,
    cited_passages,
    sanitize_citations,
    sanitize_urls,
    select_passages,
    source_ids,
)
from backend.rag.llm_provider import LLMProviderError, generate_text
from backend.rag.prompt import (
    INSUFFICIENT_CONTEXT_TOKEN,
    SYSTEM_PROMPT,
    build_user_prompt,
)

FALLBACK_ANSWER = (
    "Mình chưa tìm thấy thông tin chắc chắn cho câu hỏi này trong tài liệu hiện có. "
    "Bạn có thể hỏi rõ hơn, hoặc liên hệ BTC/TA để được xác nhận nhé."
)
PROVIDER_FAILURE_ANSWER = (
    "Mình đã tìm thấy tài liệu liên quan nhưng hiện chưa thể tạo câu trả lời. "
    "Bạn vui lòng thử lại sau nhé."
)


def _fallback() -> dict:
    return {"answer": FALLBACK_ANSWER, "sources": [], "has_evidence": False}


def generate(question: str, passages: list[dict]) -> dict:
    if not has_sufficient_evidence(passages):
        return _fallback()

    selected = select_passages(passages)
    if not selected:
        return _fallback()

    prompt = build_user_prompt(question, selected)
    try:
        answer = generate_text(SYSTEM_PROMPT, prompt)
    except LLMProviderError:
        return {
            "answer": PROVIDER_FAILURE_ANSWER,
            "sources": source_ids(selected),
            "has_evidence": True,
        }

    if answer.strip() == INSUFFICIENT_CONTEXT_TOKEN:
        return _fallback()

    cited = cited_passages(answer, selected)
    answer = sanitize_citations(answer, len(selected))
    answer = sanitize_urls(answer, cited)
    if not answer:
        return _fallback()
    return {
        "answer": attach_sources(answer, cited),
        "sources": source_ids(cited),
        "has_evidence": True,
    }
