"""Đọc kho tri thức THẬT đã ingest để dựng trang FAQ / Tra cứu.

Nguồn: backend/knowledge_base/processed/chunks.jsonl (86 chunk ở thời điểm viết).
Mỗi chunk có `heading_path` (list), `text`, `source`, `source_url` — gom nhóm theo
`heading_path[0]` cho ra đúng các danh mục thật của tài liệu, không phải danh mục bịa.

File này gitignored + tự sinh bởi backend/rag/ingest.py nên có thể CHƯA TỒN TẠI sau khi
clone repo. Mọi hàm phải trả rỗng thay vì raise để UI hiện empty state hướng dẫn chạy ingest.
"""
from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass

import streamlit as st

from config import KB_CHUNKS_PATH

# Nhóm FAQ trong tài liệu. Chunk FAQ có heading_path = [FAQ_GROUP, "<câu hỏi>"]; riêng chunk
# tiêu đề mục (chỉ 1 cấp) không có nội dung Q&A nên bị lọc bỏ khi dựng danh sách câu hỏi.
FAQ_GROUP = "CÂU HỎI THƯỜNG GẶP"


@dataclass(frozen=True)
class KBEntry:
    """1 mục kiến thức hiển thị cho sinh viên."""

    group: str
    title: str
    text: str
    source: str
    source_url: str

    @property
    def is_faq(self) -> bool:
        return self.group.upper() == FAQ_GROUP


def _strip_accents(text: str) -> str:
    """Bỏ dấu để search 'quy dinh' vẫn ra 'quy định' — sinh viên hay gõ không dấu.

    Lưu ý: 'đ' (U+0111) là một ký tự riêng, KHÔNG tách ra thành d + dấu khi normalize NFD,
    nên phải thay thủ công. Thiếu bước này thì 'diem danh' không khớp 'điểm danh'.
    """
    lowered = (text or "").lower().replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


@st.cache_data(ttl=300, show_spinner=False)
def load_entries() -> list[dict]:
    """Đọc + parse chunks.jsonl. Cache 300s để không đọc lại 86 dòng mỗi lần Streamlit rerun.

    Trả về list[dict] (không phải dataclass) vì st.cache_data cần giá trị serialize được.
    """
    path = KB_CHUNKS_PATH
    if not path.is_file():
        return []

    entries: list[dict] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                heading = record.get("heading_path") or []
                if not heading:
                    continue
                group = heading[0]
                # heading_path[1] là tiêu đề mục con (với FAQ chính là câu hỏi).
                title = heading[1] if len(heading) > 1 else group
                entries.append(
                    {
                        "group": group,
                        "title": title,
                        "text": record.get("text", ""),
                        "source": record.get("source", ""),
                        "source_url": record.get("source_url", ""),
                        "depth": len(heading),
                    }
                )
    except OSError:
        return []
    return entries


def _to_entry(raw: dict) -> KBEntry:
    return KBEntry(
        group=raw["group"],
        title=raw["title"],
        text=raw["text"],
        source=raw["source"],
        source_url=raw["source_url"],
    )


def is_available() -> bool:
    """KB đã ingest chưa — view dùng để chọn giữa nội dung thật và empty state."""
    return bool(load_entries())


def list_groups() -> list[tuple[str, int]]:
    """Danh sách (tên nhóm, số mục), nhóm FAQ luôn đứng đầu vì sinh viên hay xem nhất."""
    counts: dict[str, int] = {}
    for raw in load_entries():
        counts[raw["group"]] = counts.get(raw["group"], 0) + 1
    groups = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return sorted(groups, key=lambda kv: kv[0].upper() != FAQ_GROUP)


def get_entries(group: str | None = None, query: str = "") -> list[KBEntry]:
    """Lọc theo nhóm + tìm kiếm không dấu trên tiêu đề và nội dung.

    Với nhóm FAQ, bỏ chunk tiêu đề mục (depth == 1) vì nó chỉ chứa dòng "VII. CÂU HỎI
    THƯỜNG GẶP" chứ không phải một câu hỏi thật.
    """
    entries = load_entries()

    if group:
        entries = [e for e in entries if e["group"] == group]

    entries = [e for e in entries if not (e["group"].upper() == FAQ_GROUP and e["depth"] < 2)]

    needle = _strip_accents(query.strip())
    if needle:
        entries = [e for e in entries if needle in _strip_accents(e["title"]) or needle in _strip_accents(e["text"])]

    return [_to_entry(e) for e in entries]


def get_faq() -> list[KBEntry]:
    """Chỉ các cặp hỏi–đáp trong mục FAQ của tài liệu."""
    return get_entries(group=FAQ_GROUP)
