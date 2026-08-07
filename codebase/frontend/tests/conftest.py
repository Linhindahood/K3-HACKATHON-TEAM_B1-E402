"""Fixture dùng chung cho test frontend.

Frontend là flat-module (import `from config import ...`, `from services... import ...`) vì
Streamlit tự đặt thư mục entrypoint vào sys.path. Khi chạy bằng pytest thì không có cơ chế đó
nên conftest phải tự thêm `frontend/` vào sys.path.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

FRONTEND_DIR = Path(__file__).resolve().parent.parent
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

APP_PATH = str(FRONTEND_DIR / "app.py")


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Trỏ .local_store sang tmp_path để test không đụng dữ liệu demo thật của người dùng.

    autouse: mọi test đều phải chạy trên store sạch, quên set là dính rác từ test trước.
    """
    monkeypatch.setenv("CAMPUS247_LOCAL_STORE", str(tmp_path / "store"))
    monkeypatch.setenv("USE_MOCK_SERVICES", "1")
    return tmp_path / "store"


@pytest.fixture
def sample_ask_result():
    """AskResult giả lập câu trả lời RAG có nguồn — dùng thay cho backend thật khi test UI."""
    from api_client import AskResult

    return AskResult(
        answer="Sinh viên cần tham dự tối thiểu 80% số buổi học.",
        sources=["2_Handbook_AI_IN_ACTION.txt#quy-dinh-dao-tao"],
        has_evidence=True,
        intent="factual",
        media=[],
        error=None,
    )
