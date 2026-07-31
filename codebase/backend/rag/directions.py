"""Direction query node extraction — uses LLM-enhanced search_query from router."""
from __future__ import annotations

import re

_DEFAULT_ORIGIN = "Cổng chính VinUniversity (Main Gate)"

_FROM_TO_PATTERN = re.compile(
    r"(?:từ|tại|ở)\s+(.+?)\s+(?:đến|tới|sang|đi|về)\s+(.+)",
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

    match = _FROM_TO_PATTERN.search(text)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # No explicit origin → default to Main Gate
    return _DEFAULT_ORIGIN, text
