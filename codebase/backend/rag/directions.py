"""Direction query analysis and location node extraction V1."""
from __future__ import annotations

import re

from backend.rag.query_processing import normalize_query

_LOCATION_KEYWORDS = [
    "ở đâu",
    "chỉ đường",
    "đi thế nào",
    "đường đi",
    "đường tới",
    "tới đâu",
    "vị trí",
    "sơ đồ",
    "bản đồ",
    "location",
    "map",
    "di chuyển",
    "cách đi",
]

_FROM_TO_PATTERN = re.compile(
    r"(?:từ|tại|ở)\s+([a-zA-Z0-9\sàáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ]+?)\s+(?:đến|tới|sang|đi|về)\s+([a-zA-Z0-9\sàáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ]+)",
    re.IGNORECASE,
)



def is_location_query(question: str) -> bool:
    """Check if query pertains to campus location, maps, or directions."""
    cleaned = normalize_query(question).casefold()
    return any(keyword in cleaned for keyword in _LOCATION_KEYWORDS)


def parse_direction_nodes(question: str) -> tuple[str, str, bool]:
    """Extract origin and destination from query.

    Returns:
        tuple[origin, destination, is_location]
    """
    cleaned = normalize_query(question).strip()
    is_loc = is_location_query(cleaned)
    if not is_loc:
        return "", "", False

    match = _FROM_TO_PATTERN.search(cleaned)
    if match:
        origin = match.group(1).strip()
        destination = match.group(2).strip()
        return origin, destination, True

    # Default origin if user asks for directions without specifying starting point
    default_origin = "Cổng chính VinUniversity (Main Gate)"
    destination = cleaned
    return default_origin, destination, True
