"""Lớp gọi HTTP tới backend FastAPI (POST /ask, GET /health). Không chứa logic RAG."""
from __future__ import annotations

from dataclasses import dataclass, field

import requests
import streamlit as st

from config import BACKEND_URL, HEALTH_TIMEOUT_S, REQUEST_TIMEOUT_S


@dataclass
class AskResult:
    """Kết quả một lượt hỏi. `error` chỉ được set khi gọi backend thất bại."""

    answer: str = ""
    sources: list[str] = field(default_factory=list)
    has_evidence: bool = False
    intent: str = ""
    media: list[dict] = field(default_factory=list)
    error: str | None = None


@st.cache_resource
def get_http_session() -> requests.Session:
    """Một requests.Session dùng chung, tránh khởi tạo lại mỗi lần rerun."""
    return requests.Session()


def ask_rag(question: str) -> AskResult:
    """Gọi POST {BACKEND_URL}/ask. Không bao giờ raise ra ngoài — mọi lỗi transport/HTTP/JSON
    được gói vào AskResult.error để UI hiển thị thông báo thân thiện thay vì traceback."""
    session = get_http_session()
    try:
        response = session.post(
            f"{BACKEND_URL}/ask",
            json={"question": question},
            timeout=REQUEST_TIMEOUT_S,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return AskResult(error="⚠️ Không thể kết nối tới hệ thống. Vui lòng thử lại sau.")

    return AskResult(
        answer=data.get("answer", ""),
        sources=data.get("sources", []) or [],
        has_evidence=bool(data.get("has_evidence", False)),
        intent=data.get("intent", "") or "",
        media=data.get("media", []) or [],
    )


@st.cache_data(ttl=10)
def check_health() -> dict:
    """Gọi GET {BACKEND_URL}/health. Lỗi -> trạng thái offline tổng hợp, không raise.
    Cache 10s để header + sidebar dùng chung 1 lần gọi mỗi rerun thay vì gọi 2 lần."""
    session = get_http_session()
    try:
        response = session.get(f"{BACKEND_URL}/health", timeout=HEALTH_TIMEOUT_S)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return {"status": "offline", "ready": False}
