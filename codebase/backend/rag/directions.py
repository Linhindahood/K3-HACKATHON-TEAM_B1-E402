"""Direction query node extraction — uses LLM-enhanced search_query from router."""
from __future__ import annotations

import re

_DEFAULT_ORIGIN = "Cổng chính VinUniversity (Main Gate)"

_FROM_TO_PATTERN = re.compile(
    r"(?:từ|tại|ở)\s+(.+?)\s+(?:đến|tới|sang|đi|về)\s+(.+)",
    re.IGNORECASE,
)

_EXPLICIT_ORIGIN_PATTERN = re.compile(
    r"(?:xuất\s+phát\s+(?:từ|tại)|đi\s+từ|từ)\s+(.+?)"
    r"(?=\s*(?:,|;|\?|$)|\s+(?:đến|tới|sang|về|đi|vào|thì|tôi|mình|"
    r"chúng\s+tôi|nhóm\s+mình|hãy|muốn|cần)\b)",
    re.IGNORECASE,
)


def parse_direction_nodes(question: str, search_query: str | None = None) -> tuple[str, str]:
    """Extract origin and destination from query.

    Uses the LLM-enhanced search_query (with diacritics restored) for reliable parsing.
    Falls back to raw question if search_query is not available.

    Returns:
        tuple[origin, destination]
    """
    text = (search_query or question).strip()
    search_match = _FROM_TO_PATTERN.search(text)
    question_match = _FROM_TO_PATTERN.search(question)
    explicit_origin = _EXPLICIT_ORIGIN_PATTERN.search(question)

    if explicit_origin:
        destination_match = search_match or question_match
        destination = destination_match.group(2).strip() if destination_match else text
        return explicit_origin.group(1).strip(), destination

    if search_match:
        return search_match.group(1).strip(), search_match.group(2).strip()

    if question_match:
        return question_match.group(1).strip(), question_match.group(2).strip()

    # No explicit origin → default to Main Gate
    return _DEFAULT_ORIGIN, text
