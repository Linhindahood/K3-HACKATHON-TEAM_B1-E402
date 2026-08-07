"""Seam cho luồng chat.

Hôm nay chỉ ủy quyền thẳng cho `api_client.ask_rag` (POST /ask — endpoint THẬT đang chạy).
Khi backend bổ sung `POST /chat` có conversation_id/multi-turn, chỉ sửa hàm này; view và
`api_client` không phải đổi gì.

Tách riêng còn để test monkeypatch 1 chỗ duy nhất thay vì patch xuyên qua tầng HTTP.
"""
from __future__ import annotations

from api_client import AskResult, ask_rag


def send_message(question: str, *, conversation_id: str = "") -> AskResult:
    """Gửi 1 lượt hỏi tới backend RAG.

    `conversation_id` hiện chưa dùng: backend stateless, mỗi request độc lập. Giữ tham số để
    khi chuyển sang /chat không phải đổi chữ ký ở phía view.
    """
    return ask_rag(question)
