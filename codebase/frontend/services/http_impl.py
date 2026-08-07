"""Bản HTTP của các service — dành cho khi backend đã có endpoint thật.

CHƯA ĐƯỢC BẬT: đặt USE_MOCK_SERVICES=0 để dùng. Backend hiện chỉ có /ask + /health nên bật
lúc này sẽ báo lỗi kết nối (đúng như thiết kế: thà báo lỗi rõ còn hơn bịa dữ liệu).

Cùng chữ ký với `mock_impl` để `factory.get_services()` hoán đổi mà view không biết khác biệt.
"""
from __future__ import annotations

from datetime import date

import requests

from api_client import get_http_session
from config import BACKEND_URL, REQUEST_TIMEOUT_S
from services.models import (
    HandoverDraft,
    HandoverRequest,
    ScheduleItem,
    ServiceResult,
    StudentProfile,
    Ticket,
    TicketDraft,
)

_TIMEOUT_MSG = "⚠️ Không thể kết nối tới hệ thống. Vui lòng thử lại sau."


def _request(method: str, path: str, **kwargs) -> ServiceResult:
    """Gọi HTTP và bọc mọi lỗi transport/HTTP/JSON vào ServiceResult.error."""
    try:
        response = get_http_session().request(
            method, f"{BACKEND_URL}{path}", timeout=REQUEST_TIMEOUT_S, **kwargs
        )
        response.raise_for_status()
        return ServiceResult(data=response.json())
    except (requests.RequestException, ValueError):
        return ServiceResult(error=_TIMEOUT_MSG)


def get_profile() -> ServiceResult:
    result = _request("GET", "/profile")
    if not result.ok:
        return result
    return ServiceResult(data=StudentProfile(**result.data, is_demo=False))


def get_schedule(student_id: str, start: date, end: date) -> ServiceResult:
    result = _request(
        "GET",
        "/schedule",
        params={"student_id": student_id, "start": start.isoformat(), "end": end.isoformat()},
    )
    if not result.ok:
        return result
    items = [ScheduleItem(**item, is_demo=False) for item in result.data.get("items", [])]
    return ServiceResult(data=items)


def create_ticket(draft: TicketDraft) -> ServiceResult:
    # Không gửi `department`/`status`: đó là business rule của backend, client không được set.
    payload = {
        "subject": draft.subject,
        "category": draft.category,
        "description": draft.description,
        "priority": draft.priority,
        "student_id": draft.student_id,
        "source_question": draft.source_question,
        "source_answer": draft.source_answer,
        "source_intent": draft.source_intent,
        "has_evidence": draft.has_evidence,
        "source_refs": draft.source_refs,
    }
    result = _request("POST", "/tickets", json=payload)
    if not result.ok:
        return result
    return ServiceResult(data=Ticket.from_dict(result.data))


def list_tickets(student_id: str = "", status: str | None = None) -> ServiceResult:
    params = {k: v for k, v in {"student_id": student_id, "status": status}.items() if v}
    result = _request("GET", "/tickets", params=params)
    if not result.ok:
        return result
    return ServiceResult(data=[Ticket.from_dict(t) for t in result.data.get("items", [])])


def get_ticket(ticket_id: str) -> ServiceResult:
    result = _request("GET", f"/tickets/{ticket_id}")
    if not result.ok:
        return result
    return ServiceResult(data=Ticket.from_dict(result.data))


def update_ticket_status(ticket_id: str, new_status: str, *, actor: str = "", note: str = "") -> ServiceResult:
    result = _request("POST", f"/tickets/{ticket_id}/status", json={"status": new_status, "note": note})
    if not result.ok:
        return result
    return ServiceResult(data=Ticket.from_dict(result.data))


def request_handover(draft: HandoverDraft) -> ServiceResult:
    result = _request(
        "POST",
        "/handover",
        json={
            "question": draft.question,
            "answer_excerpt": draft.answer_excerpt,
            "reason_code": draft.reason_code,
            "severity": draft.severity,
            "ticket_id": draft.ticket_id,
            "student_id": draft.student_id,
        },
    )
    if not result.ok:
        return result
    return ServiceResult(data=HandoverRequest.from_dict(result.data))


def list_handovers(student_id: str = "") -> ServiceResult:
    result = _request("GET", "/handover", params={"student_id": student_id} if student_id else None)
    if not result.ok:
        return result
    return ServiceResult(data=[HandoverRequest.from_dict(h) for h in result.data.get("items", [])])
