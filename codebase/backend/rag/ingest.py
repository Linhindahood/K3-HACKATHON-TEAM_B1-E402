"""Offline preparation of the RAG corpus.

The command produces deterministic chunks plus dense and lexical indexes.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

from backend import config

SCHEMA_VERSION = "1"
MAX_CHARS = 1_200

ROOM_BOOKING_URL = "https://library.vinuni.edu.vn/room-booking/"
LIBRARY_HOURS_URL = "https://library.vinuni.edu.vn/about-us/hours-and-access/"

_SOURCES = {
    "2_Handbook_AI_IN_ACTION.txt": {"kind": "handbook", "priority": 1},
    "4_gio_mo_cua_library.txt": {"kind": "library", "priority": 2},
    "6_loai_phong_va_huong_dan_dat_phong.txt": {
        "kind": "library",
        "priority": 3,
    },
}
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_ROMAN_HEADING_RE = re.compile(r"^[IVXLCDM]+\.\s*\S+", re.IGNORECASE)
_NUMBERED_HEADING_RE = re.compile(r"^\d+\.\s+[A-ZÀ-ỸĐ0-9]")
_FAQ_RE = re.compile(r"^\d+\..+\?\s*$")
_ROOM_RE = re.compile(r"^Phòng\s+[A-Z]\d+\s*:\s*$", re.IGNORECASE)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"\s+", " ", value).strip()


def _slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.decode().lower()).strip("-")


def is_url_only(text: str) -> bool:
    """Return whether non-empty lines contain URLs and no semantic prose."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return bool(lines) and all(_URL_RE.fullmatch(line) for line in lines)


_PLACEHOLDER_PATTERNS = [
    re.compile(r"điền (?:dữ liệu|thông tin|nội dung)", re.IGNORECASE),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"bổ sung thông tin vào đây", re.IGNORECASE),
]


def validate_content_preflight(documents: list[dict]) -> None:
    """Ensure raw documents do not contain placeholder instructions before chunking."""
    for document in documents:
        text = document.get("text", "")
        for pattern in _PLACEHOLDER_PATTERNS:
            if pattern.search(text):
                raise ValueError(
                    f"Content preflight failed: placeholder detected in {document['source']}"
                )


def load_raw_documents() -> list[dict]:
    """Load only text sources approved for the current RAG scope."""
    documents = []
    for source, metadata in _SOURCES.items():
        path = config.KNOWLEDGE_BASE_RAW_DIR / source
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8-sig").strip()
        documents.append(
            {
                "source": source,
                "kind": metadata["kind"],
                "priority": metadata["priority"],
                "text": text,
                "source_hash": _sha256(text),
            }
        )
    validate_content_preflight(documents)
    return documents



def _is_upper_heading(line: str) -> bool:
    letters = [character for character in line if character.isalpha()]
    return len(letters) >= 5 and all(character.isupper() for character in letters)


def _clean_heading(line: str) -> str:
    line = re.sub(r"^(?:[IVXLCDM]+|\d+)\.\s*", "", line).strip()
    return line.rstrip(":").strip()


def _is_child_heading(line: str, kind: str) -> bool:
    if _FAQ_RE.match(line) or _ROOM_RE.match(line):
        return True
    if _NUMBERED_HEADING_RE.match(line) and _is_upper_heading(line):
        return True
    if _is_upper_heading(line):
        return True
    if (
        kind == "library"
        and line.endswith(":")
        and len(line) <= 90
        and not line.casefold().startswith("bước ")
    ):
        return True
    return kind == "handbook" and line.upper().startswith("GIAI ĐOẠN ")


def _source_url(kind: str, heading_path: list[str]) -> str | None:
    if kind != "library":
        return None
    context = " ".join(heading_path).casefold()
    if any(term in context for term in ("đặt phòng", "danh sách phòng", "phòng a")):
        return ROOM_BOOKING_URL
    return LIBRARY_HOURS_URL


def _split_long(text: str) -> list[str]:
    """Split an oversized section at paragraph boundaries without overlap."""
    if len(text) <= MAX_CHARS:
        return [text]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if len(paragraphs) == 1:
        paragraphs = [line.strip() for line in text.splitlines() if line.strip()]

    parts: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > MAX_CHARS:
            if current:
                parts.append(current)
                current = ""
            parts.extend(
                paragraph[start : start + MAX_CHARS]
                for start in range(0, len(paragraph), MAX_CHARS)
            )
            continue
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > MAX_CHARS:
            parts.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def _parse_document(document: dict) -> list[dict]:
    """Parse headings while keeping FAQ answers and room records atomic."""
    kind = document["kind"]
    parent = _clean_heading(document["source"])
    title = parent
    buffer: list[str] = []
    drafts: list[dict] = []

    def flush() -> None:
        nonlocal buffer
        text = "\n".join(buffer).strip()
        if not text:
            return
        heading_path = [parent] if title == parent else [parent, title]
        for part_number, part in enumerate(_split_long(text), start=1):
            part_path = list(heading_path)
            if len(text) > MAX_CHARS:
                part_path.append(f"Phần {part_number}")
            drafts.append(
                {
                    "source": document["source"],
                    "kind": kind,
                    "priority": document["priority"],
                    "heading_path": part_path,
                    "text": part,
                    "source_url": _source_url(kind, heading_path),
                }
            )
        buffer = []

    for raw_line in document["text"].splitlines():
        line = raw_line.strip()
        if not line:
            if buffer and buffer[-1] != "":
                buffer.append("")
            continue

        is_parent = (
            kind == "handbook"
            and _ROMAN_HEADING_RE.match(line)
            or kind == "library"
            and _NUMBERED_HEADING_RE.match(line)
            and _is_upper_heading(line)
        )
        if is_parent:
            flush()
            parent = _clean_heading(line)
            title = parent
            buffer = [line]
        elif _is_child_heading(line, kind):
            flush()
            title = _clean_heading(line)
            buffer = [line]
        else:
            buffer.append(line)
    flush()
    return drafts


def _deduplication_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if _URL_RE.search(line):
            continue
        line = re.sub(r"^\s*\d+\.\s+", "", line)
        if line.strip():
            lines.append(line)
    return _normalise("\n".join(lines)).casefold()


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Create deterministic, structure-aware chunks and remove duplicates."""
    drafts = []
    for document in sorted(documents, key=lambda item: item["priority"]):
        drafts.extend(_parse_document(document))

    unique: list[dict] = []
    by_hash: dict[str, dict] = {}
    used_ids: set[str] = set()
    for draft in drafts:
        content_hash = _sha256(_deduplication_text(draft["text"]))
        if content_hash in by_hash:
            by_hash[content_hash].setdefault("duplicate_sources", []).append(
                draft["source"]
            )
            continue

        base_id = _slug("-".join(draft["heading_path"])) or "chunk"
        chunk_id = base_id
        if chunk_id in used_ids:
            chunk_id = f"{base_id}-{content_hash[:8]}"
        used_ids.add(chunk_id)

        chunk = {
            "chunk_id": chunk_id,
            "content_hash": content_hash,
            "source": draft["source"],
            "heading_path": draft["heading_path"],
            "text": draft["text"],
            "embedding_text": (
                f"{' > '.join(draft['heading_path'])}\n{draft['text']}"
            ),
            "source_url": draft["source_url"],
        }
        unique.append(chunk)
        by_hash[content_hash] = chunk
    return unique


def _source_inventory(documents: list[dict]) -> list[dict]:
    indexed = {document["source"]: document for document in documents}
    skipped_reasons = {
        "1_map.jpg": "image requires a verified text sidecar from the data role",
        "3_link_vi_tri.txt": "URL-only metadata",
        "5_ket_qua_khoa_1.txt": "outside the current product scope",
    }
    inventory = []
    for path in sorted(config.KNOWLEDGE_BASE_RAW_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.name in indexed:
            inventory.append(
                {
                    "source": path.name,
                    "status": "indexed",
                    "source_hash": indexed[path.name]["source_hash"],
                }
            )
        else:
            inventory.append(
                {
                    "source": path.name,
                    "status": "skipped",
                    "reason": skipped_reasons.get(
                        path.name, "placeholder or source not approved for RAG"
                    ),
                }
            )
    return inventory


def write_artifacts(
    documents: list[dict],
    chunks: list[dict],
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Write reproducible JSONL chunks and a corpus manifest."""
    destination = output_dir or config.KNOWLEDGE_BASE_PROCESSED_DIR
    destination.mkdir(parents=True, exist_ok=True)
    chunks_path = destination / "chunks.jsonl"
    manifest_path = destination / "manifest.json"

    chunks_payload = "".join(
        json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n"
        for chunk in chunks
    )
    duplicate_count = sum(
        len(chunk.get("duplicate_sources", [])) for chunk in chunks
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "chunk_count": len(chunks),
        "duplicate_count": duplicate_count,
        "sources": _source_inventory(documents),
    }
    chunks_path.write_text(chunks_payload, encoding="utf-8", newline="\n")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return chunks_path, manifest_path


def build_index(chunks: list[dict]) -> tuple[Path, Path, Path]:
    """Build local E5 embeddings and an exact dense FAISS index."""
    from backend.rag.embedding_artifacts import build_embedding_artifacts

    return build_embedding_artifacts(chunks)


def build_lexical_index(chunks: list[dict]) -> Path:
    """Build the BM25S index from the same ordered chunks as dense search."""
    from backend.rag.lexical_artifacts import build_lexical_artifact

    return build_lexical_artifact(chunks)


def main() -> None:
    documents = load_raw_documents()
    chunks = chunk_documents(documents)
    chunks_path, manifest_path = write_artifacts(documents, chunks)
    embeddings_path, index_path, embedding_manifest_path = build_index(chunks)
    lexical_manifest_path = build_lexical_index(chunks)
    print(f"Wrote {len(chunks)} chunks to {chunks_path}")
    print(f"Wrote manifest to {manifest_path}")
    print(f"Wrote embeddings to {embeddings_path}")
    print(f"Wrote dense index to {index_path}")
    print(f"Wrote embedding manifest to {embedding_manifest_path}")
    print(f"Wrote lexical index to {lexical_manifest_path.parent}")


if __name__ == "__main__":
    main()
