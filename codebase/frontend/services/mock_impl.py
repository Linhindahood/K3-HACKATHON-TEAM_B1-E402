"""Bản mock của các service chưa có API backend (ticket, lịch học, hồ sơ, handover).

Backend hiện chỉ có POST /ask + GET /health nên toàn bộ dữ liệu ở đây là DEMO DATA sinh tại
frontend, lưu xuống `.local_store/*.jsonl` để sống sót qua refresh/restart.

Mọi hàm trả về `ServiceResult` và KHÔNG raise — view chỉ cần kiểm tra `.ok`.
"""
from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta, timezone

from config import DEFAULT_DEPARTMENT, DEPARTMENT_BY_CATEGORY
from services import store
from services.models import (
    ALLOWED_TRANSITIONS,
    PRIORITY_HIGH,
    PRIORITY_NORMAL,
    PRIORITY_URGENT,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    HandoverDraft,
    HandoverRequest,
    ScheduleItem,
    ServiceResult,
    StudentProfile,
    Ticket,
    TicketDraft,
    TicketEvent,
)

TICKETS_FILE = "tickets.jsonl"
HANDOVERS_FILE = "handovers.jsonl"

# Hồ sơ sinh viên DEMO — backend chưa có auth, đây là dữ liệu giả để minh họa luồng.
DEMO_PROFILE = StudentProfile(
    student_id="SV2026001",
    full_name="Nguyễn Văn An",
    class_name="AI-K3-B1",
    major="Trí tuệ nhân tạo ứng dụng",
    cohort="Khóa 3 (2026)",
    email="an.nv.demo@vinuni.edu.vn",
)

# Thời khóa biểu DEMO. Backend không có API lịch học, cũng không có dữ liệu lịch cá nhân
# trong kho tri thức -> đây hoàn toàn là số liệu minh họa, UI phải gắn nhãn DEMO DATA.
_DEMO_WEEK_TEMPLATE: list[dict] = [
    {"offset": 0, "start": "08:30", "end": "11:30", "subject": "Machine Learning cơ bản", "room": "A101", "lecturer": "TS. Trần Minh Quang"},
    {"offset": 0, "start": "13:30", "end": "16:30", "subject": "Lab: Feature Engineering", "room": "A102", "lecturer": "ThS. Lê Thu Hà"},
    {"offset": 1, "start": "08:30", "end": "11:30", "subject": "Deep Learning", "room": "A103", "lecturer": "TS. Phạm Đức Anh"},
    {"offset": 2, "start": "08:30", "end": "11:30", "subject": "NLP ứng dụng", "room": "B201", "lecturer": "TS. Ngô Bảo Châu"},
    {"offset": 2, "start": "13:30", "end": "16:30", "subject": "Seminar doanh nghiệp", "room": "Hội trường B", "lecturer": "Khách mời"},
    {"offset": 3, "start": "08:30", "end": "11:30", "subject": "Computer Vision", "room": "A101", "lecturer": "TS. Vũ Hải Đăng"},
    {"offset": 4, "start": "08:30", "end": "11:30", "subject": "Capstone Project", "room": "Khu tự học", "lecturer": "Mentor nhóm"},
]

_WEEKDAY_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- Profile ---------------------------------------------------------------
def get_profile() -> ServiceResult:
    return ServiceResult(data=DEMO_PROFILE)


# --- Schedule --------------------------------------------------------------
def get_schedule(student_id: str, start: date, end: date) -> ServiceResult:
    """Sinh lịch DEMO cho khoảng ngày [start, end]. Cuối tuần trả rỗng để UI có empty state thật."""
    try:
        items: list[ScheduleItem] = []
        cursor = start
        while cursor <= end:
            weekday_idx = cursor.weekday()
            for entry in _DEMO_WEEK_TEMPLATE:
                if entry["offset"] != weekday_idx:
                    continue
                items.append(
                    ScheduleItem(
                        item_id=f"{cursor.isoformat()}-{entry['start']}-{entry['room']}",
                        date=cursor.isoformat(),
                        weekday=_WEEKDAY_VI[weekday_idx],
                        start_time=entry["start"],
                        end_time=entry["end"],
                        subject=entry["subject"],
                        room=entry["room"],
                        lecturer=entry["lecturer"],
                    )
                )
            cursor += timedelta(days=1)
        items.sort(key=lambda it: (it.date, it.start_time))
        return ServiceResult(data=items)
    except Exception as exc:  # pragma: no cover - phòng thủ, không nên xảy ra
        return ServiceResult(error=f"Không tải được lịch học: {exc}")


# --- Tickets ---------------------------------------------------------------
def _department_for(category: str) -> str:
    """Routing: department LUÔN suy ra từ category theo business rule, user không tự set được."""
    return DEPARTMENT_BY_CATEGORY.get(category, DEFAULT_DEPARTMENT)


def _new_ticket_id() -> str:
    return f"TK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"


def create_ticket(draft: TicketDraft) -> ServiceResult:
    """Tạo ticket mới. Trả lỗi rõ ràng nếu thiếu thông tin bắt buộc — không tạo ticket rỗng."""
    subject = (draft.subject or "").strip()
    description = (draft.description or "").strip()
    if not subject:
        return ServiceResult(error="Vui lòng nhập tiêu đề yêu cầu.")
    if not description:
        return ServiceResult(error="Vui lòng mô tả chi tiết vấn đề bạn gặp phải.")

    now = _now_iso()
    ticket = Ticket(
        ticket_id=_new_ticket_id(),
        subject=subject,
        category=draft.category or "khac",
        department=_department_for(draft.category or "khac"),
        description=description,
        status=STATUS_OPEN,
        priority=draft.priority or PRIORITY_NORMAL,
        created_at=now,
        updated_at=now,
        student_id=draft.student_id,
        source_question=draft.source_question,
        source_answer=draft.source_answer,
        source_intent=draft.source_intent,
        has_evidence=draft.has_evidence,
        source_refs=list(draft.source_refs or []),
        conversation_excerpt=list(draft.conversation_excerpt or []),
        events=[TicketEvent(at=now, actor="Hệ thống", kind="created", note=f"Định tuyến tới {_department_for(draft.category or 'khac')}")],
    )

    try:
        store.append(TICKETS_FILE, ticket.to_dict())
    except OSError as exc:
        # Không được báo "đã tạo ticket" khi ghi thất bại.
        return ServiceResult(error=f"Không lưu được yêu cầu: {exc}")
    return ServiceResult(data=ticket)


def list_tickets(student_id: str = "", status: str | None = None) -> ServiceResult:
    try:
        records = store.read_all(TICKETS_FILE)
        tickets = [Ticket.from_dict(r) for r in records]
    except OSError as exc:
        return ServiceResult(error=f"Không đọc được danh sách yêu cầu: {exc}")

    if student_id:
        tickets = [t for t in tickets if not t.student_id or t.student_id == student_id]
    if status:
        tickets = [t for t in tickets if t.status == status]
    tickets.sort(key=lambda t: t.created_at, reverse=True)
    return ServiceResult(data=tickets)


def get_ticket(ticket_id: str) -> ServiceResult:
    result = list_tickets()
    if not result.ok:
        return result
    for ticket in result.data:
        if ticket.ticket_id == ticket_id:
            return ServiceResult(data=ticket)
    return ServiceResult(error=f"Không tìm thấy yêu cầu {ticket_id}.")


def update_ticket_status(ticket_id: str, new_status: str, *, actor: str = "Nhân viên hỗ trợ", note: str = "") -> ServiceResult:
    """Đổi trạng thái ticket, chặn các bước nhảy không hợp lệ theo ALLOWED_TRANSITIONS."""
    try:
        records = store.read_all(TICKETS_FILE)
    except OSError as exc:
        return ServiceResult(error=f"Không đọc được yêu cầu: {exc}")

    tickets = [Ticket.from_dict(r) for r in records]
    target = next((t for t in tickets if t.ticket_id == ticket_id), None)
    if target is None:
        return ServiceResult(error=f"Không tìm thấy yêu cầu {ticket_id}.")

    allowed = ALLOWED_TRANSITIONS.get(target.status, ())
    if new_status not in allowed:
        return ServiceResult(error=f"Không thể chuyển {target.status} → {new_status}.")

    target.status = new_status
    target.updated_at = _now_iso()
    target.events.append(TicketEvent(at=target.updated_at, actor=actor, kind="status_changed", note=note or f"→ {new_status}"))

    try:
        store.write_all(TICKETS_FILE, [t.to_dict() for t in tickets])
    except OSError as exc:
        return ServiceResult(error=f"Không lưu được thay đổi: {exc}")
    return ServiceResult(data=target)


def next_status_for(status: str) -> str:
    """Bước tiếp theo gợi ý cho nút 'Mô phỏng xử lý (DEMO)'."""
    allowed = ALLOWED_TRANSITIONS.get(status, ())
    return allowed[0] if allowed else ""


# --- Handover --------------------------------------------------------------
def request_handover(draft: HandoverDraft) -> ServiceResult:
    """Ghi nhận yêu cầu gặp người thật.

    `eta_minutes` là ước tính DEMO (ngẫu nhiên có kiểm soát), KHÔNG phải SLA thật của trường.
    """
    now = _now_iso()
    handover = HandoverRequest(
        handover_id=f"HO-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}",
        ticket_id=draft.ticket_id,
        reason_code=draft.reason_code,
        severity=draft.severity,
        status="WAITING_FOR_STAFF",
        requested_at=now,
        question=draft.question,
        answer_excerpt=draft.answer_excerpt,
        assigned_to="Hàng đợi hỗ trợ sinh viên",
        eta_minutes=random.choice([10, 15, 20, 30]),
        student_id=draft.student_id,
    )
    try:
        store.append(HANDOVERS_FILE, handover.to_dict())
    except OSError as exc:
        return ServiceResult(error=f"Không gửi được yêu cầu gặp nhân viên: {exc}")
    return ServiceResult(data=handover)


def list_handovers(student_id: str = "") -> ServiceResult:
    try:
        records = store.read_all(HANDOVERS_FILE)
        items = [HandoverRequest.from_dict(r) for r in records]
    except OSError as exc:
        return ServiceResult(error=f"Không đọc được danh sách handover: {exc}")
    if student_id:
        items = [h for h in items if not h.student_id or h.student_id == student_id]
    items.sort(key=lambda h: h.requested_at, reverse=True)
    return ServiceResult(data=items)


def suggest_priority(*, urgent: bool = False, sensitive: bool = False, unsupported: bool = False) -> str:
    """Gợi ý priority từ tín hiệu escalation. User luôn được phép override trong form."""
    if urgent:
        return PRIORITY_URGENT
    if sensitive or unsupported:
        return PRIORITY_HIGH
    return PRIORITY_NORMAL
