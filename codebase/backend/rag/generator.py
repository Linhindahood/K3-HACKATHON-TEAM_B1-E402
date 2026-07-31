"""Thin orchestration for grounded answer generation."""
from __future__ import annotations

from backend.rag.citation_validator import validate_and_sanitize_citations
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
from backend.rag.response_policy import (
    NO_EVIDENCE_ANSWER,
    PROVIDER_FAILURE_ANSWER,
    strip_internal_leakage,
)

FALLBACK_ANSWER = NO_EVIDENCE_ANSWER


def _fallback() -> dict:
    return {"answer": NO_EVIDENCE_ANSWER, "sources": [], "has_evidence": False}


def generate(question: str, passages: list[dict]) -> dict:
    if not has_sufficient_evidence(passages):
        return _fallback()

    selected = select_passages(passages)
    if not selected:
        return _fallback()

    prompt = build_user_prompt(question, selected)
    try:
        raw_answer = generate_text(SYSTEM_PROMPT, prompt)
    except LLMProviderError:
        return {
            "answer": PROVIDER_FAILURE_ANSWER,
            "sources": source_ids(selected),
            "has_evidence": True,
        }

    if raw_answer.strip() == INSUFFICIENT_CONTEXT_TOKEN:
        return _fallback()

    cleaned_answer, valid_sources, is_valid = validate_and_sanitize_citations(
        raw_answer, selected
    )
    if not is_valid:
        return _fallback()

    cited = cited_passages(cleaned_answer, selected)
    if not cited:

        cited = selected[:1]
    final_sources = valid_sources if valid_sources else source_ids(cited)

    answer = sanitize_citations(cleaned_answer, len(selected))
    answer = sanitize_urls(answer, cited)
    if not answer:
        return _fallback()

    return {
        "answer": attach_sources(answer, cited),
        "sources": final_sources,
        "has_evidence": True,
    }

