"""Small, deterministic query transformations for dense and lexical search."""
from __future__ import annotations

import re
import unicodedata

_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def normalize_query(query: str) -> str:
    normalized = unicodedata.normalize("NFC", query)
    return re.sub(r"\s+", " ", normalized).strip()


def _without_accents(token: str) -> str:
    token = token.replace("đ", "d").replace("Đ", "D")
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", token)
        if unicodedata.category(character) != "Mn"
    )


def lexical_tokens(text: str) -> list[str]:
    """Return lowercase Vietnamese tokens plus accentless variants."""
    tokens = []
    for token in _TOKEN_RE.findall(normalize_query(text).casefold()):
        tokens.append(token)
        accentless = _without_accents(token)
        if accentless != token:
            tokens.append(accentless)
    return tokens
