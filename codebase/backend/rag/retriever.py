"""[Minh] Nhận câu hỏi, trả về top-k đoạn tài liệu liên quan nhất + nguồn.

Format output chốt sẵn để generator.py cắm vào không cần chờ ingest/FAISS xong:
    [{"text": "...", "source": "noi_quy.md#trang-phuc", "score": 0.82}, ...]
"""
from __future__ import annotations

TOP_K = 4


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """Stub: chưa nối FAISS index thật, trả về danh sách rỗng.

    TODO(Minh): load index từ config.FAISS_INDEX_DIR (xem rag/ingest.py),
    embed `question`, tìm top_k đoạn gần nhất, trả kèm "source" và "score".
    """
    return []
