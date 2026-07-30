"""Passage selection plus deterministic source and URL handling."""
from __future__ import annotations

import re

from backend import config

_URL_RE = re.compile(r"https?://[^\s<>\]]+")
_CITATION_RE = re.compile(r"\[S(\d+)\]")
_URL_TRAILING = ".,;:!?)]}"


def select_passages(passages: list[dict]) -> list[dict]:
    selected = []
    seen = set()
    for passage in passages:
        source = passage.get("source", "").strip()
        text = passage.get("text", "").strip()
        if not source or not text or source in seen:
            continue
        selected.append(passage)
        seen.add(source)
        if len(selected) == config.GENERATOR_MAX_PASSAGES:
            break
    return selected


def source_ids(passages: list[dict]) -> list[str]:
    return list(dict.fromkeys(passage["source"] for passage in passages))


def cited_passages(answer: str, passages: list[dict]) -> list[dict]:
    cited = []
    seen = set()
    for raw_index in _CITATION_RE.findall(answer):
        index = int(raw_index) - 1
        if 0 <= index < len(passages) and index not in seen:
            cited.append(passages[index])
            seen.add(index)
    return cited


def sanitize_citations(answer: str, passage_count: int) -> str:
    def replace(match: re.Match) -> str:
        index = int(match.group(1))
        return match.group(0) if 1 <= index <= passage_count else ""

    return _CITATION_RE.sub(replace, answer)


def _allowed_urls(passages: list[dict]) -> set[str]:
    return {
        url
        for passage in passages
        if (url := passage.get("source_url"))
        and url.startswith(("https://", "http://"))
    }


def sanitize_urls(answer: str, passages: list[dict]) -> str:
    allowed = _allowed_urls(passages)

    def replace(match: re.Match) -> str:
        raw = match.group(0)
        url = raw.rstrip(_URL_TRAILING)
        suffix = raw[len(url) :]
        return raw if url in allowed else suffix

    return _URL_RE.sub(replace, answer).strip()


def attach_sources(answer: str, passages: list[dict]) -> str:
    lines = []
    seen_urls = set()
    for passage in passages:
        source = passage["source"]
        url = passage.get("source_url")
        if url and url not in seen_urls and url not in answer:
            lines.append(f"- [{source}]({url})")
            seen_urls.add(url)
        else:
            lines.append(f"- {source}")
    return f"{answer.rstrip()}\n\nNguồn tham khảo:\n" + "\n".join(lines)
