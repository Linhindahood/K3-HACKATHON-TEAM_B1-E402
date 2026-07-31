"""Machine-owned citation extraction and validation for grounded answers."""
from __future__ import annotations

import re


def extract_citation_markers(text: str) -> list[str]:
    """Extract all citation markers like [S1], [S2] from text in order."""
    matches = re.findall(r"\[S(\d+)\]", text)
    return [f"S{m}" for m in matches]


def validate_and_sanitize_citations(
    answer: str, passages: list[dict]
) -> tuple[str, list[str], bool]:
    """Validate citations in LLM answer against whitelisted passages.

    Returns:
        tuple[cleaned_answer, valid_sources, is_valid]
    """
    if not answer or not passages:
        return answer, [], False

    passage_map = {}
    for idx, passage in enumerate(passages, start=1):
        pid = f"S{idx}"
        passage_map[pid] = passage

    extracted_ids = extract_citation_markers(answer)
    valid_sources = []
    seen_sources = set()

    for pid in extracted_ids:
        if pid in passage_map:
            source = passage_map[pid].get("source")
            if source and source not in seen_sources:
                seen_sources.add(source)
                valid_sources.append(source)

    # Strip any orphaned citation markers [Sx] that do not exist in passage_map
    def _replace_marker(match: re.Match) -> str:
        marker_id = f"S{match.group(1)}"
        if marker_id in passage_map:
            return match.group(0)
        return ""

    cleaned_answer = re.sub(r"\[S(\d+)\]", _replace_marker, answer)
    cleaned_answer = re.sub(r"\s+", " ", cleaned_answer)
    cleaned_answer = re.sub(r"\s+([.,;:!?])", r"\1", cleaned_answer).strip()


    # If LLM cited invalid markers exclusively, invalidate response
    if extracted_ids and not valid_sources:
        return cleaned_answer, [], False

    return cleaned_answer, valid_sources, True
