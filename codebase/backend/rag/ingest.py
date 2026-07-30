"""[Minh] Đọc knowledge_base/raw/*.md → chunk theo heading → embed → lưu FAISS index.

Chạy độc lập (không phải lúc nào cũng chạy trong FastAPI process):
    python -m backend.rag.ingest
"""
from __future__ import annotations

from backend import config


def load_raw_documents() -> list[dict]:
    """TODO(Minh): đọc từng file trong config.KNOWLEDGE_BASE_RAW_DIR,
    trả về [{"source": "noi_quy.md", "text": "..."}]."""
    return []


def chunk_documents(documents: list[dict]) -> list[dict]:
    """TODO(Minh): chia theo heading Markdown (`##`), mỗi mục = 1 chunk.
    Output ghi ra config.KNOWLEDGE_BASE_PROCESSED_DIR / "chunks.jsonl"."""
    return []


def build_index(chunks: list[dict]) -> None:
    """TODO(Minh): embed từng chunk, lưu FAISS index vào config.FAISS_INDEX_DIR."""
    raise NotImplementedError


def main() -> None:
    documents = load_raw_documents()
    chunks = chunk_documents(documents)
    build_index(chunks)


if __name__ == "__main__":
    main()
