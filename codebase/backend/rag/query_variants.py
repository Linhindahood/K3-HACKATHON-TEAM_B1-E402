"""Query variant generation for multi-vector and lexical retrieval V1."""
from __future__ import annotations

import unicodedata

from backend.rag.query_processing import normalize_query


def _strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", text)
        if unicodedata.category(character) != "Mn"
    )


def _has_vietnamese_accents(text: str) -> bool:
    """Check if string contains Vietnamese diacritic characters."""
    accented_chars = "àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ"
    return any(character in accented_chars for character in text)


def generate_query_variants(
    question: str, search_query: str | None = None
) -> dict[str, str]:
    """Generate search variants (original, accentless if needed, enhanced) for BM25 and Dense search."""
    cleaned_original = normalize_query(question).strip()

    variants = {
        "original": cleaned_original,
    }

    # Only add accentless variant if the original query lacks Vietnamese accents
    if not _has_vietnamese_accents(cleaned_original):
        variants["accentless"] = _strip_accents(cleaned_original)

    if search_query and search_query.strip() and search_query.strip() != cleaned_original:
        variants["enhanced"] = normalize_query(search_query).strip()

    return variants

