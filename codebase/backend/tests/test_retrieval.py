"""[Minh] Test nhanh retriever có tìm đúng đoạn không.

Chạy: pytest codebase/backend/tests/test_retrieval.py
"""
from backend.rag import retriever


def test_retrieve_returns_list():
    result = retriever.retrieve("giờ vào học là mấy giờ?")
    assert isinstance(result, list)
