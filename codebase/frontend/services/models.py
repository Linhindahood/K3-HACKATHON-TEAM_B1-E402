"""Dataclass dùng chung cho mọi service (mock lẫn HTTP).

Đây là *contract* giữa view và service: view chỉ đọc/ghi các dataclass này, không bao giờ
đụng vào JSON thô hay endpoint. Nhờ vậy đổi mock -> API thật không cần sửa view.

Mọi bản ghi demo đều mang cờ `is_demo` để UI gắn nhãn DEMO DATA — tránh sinh viên hiểu nhầm
đây là dữ liệu thật của trường.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# --- Ticket status lifecycle ------------------------------------------------
STATUS_OPEN = "OPEN"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_WAITING = "WAITING"
STATUS_RESOLVED = "RESOLVED"
STATUS_CLOSED = "CLOSED"

# Chuyển trạng thái hợp lệ. mock_impl validate theo bảng này để không nhảy trạng thái bừa
# (vd RESOLVED -> OPEN). Đóng ticket thì cho phép từ bất kỳ trạng thái nào.
ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
    STATUS_OPEN: (STATUS_IN_PROGRESS, STATUS_CLOSED),
    STATUS_IN_PROGRESS: (STATUS_WAITING, STATUS_RESOLVED, STATUS_CLOSED),
    STATUS_WAITING: (STATUS_IN_PROGRESS, STATUS_CLOSED),
    STATUS_RESOLVED: (STATUS_IN_PROGRESS, STATUS_CLOSED),
    STATUS_CLOSED: (),
}

# --- Priority ---------------------------------------------------------------
PRIORITY_LOW = "LOW"
PRIORITY_NORMAL = "NORMAL"
PRIORITY_HIGH = "HIGH"
PRIORITY_URGENT = "URGENT"

PRIORITIES = (PRIORITY_LOW, PRIORITY_NORMAL, PRIORITY_HIGH, PRIORITY_URGENT)

# --- Handover severity ------------------------------------------------------
SEVERITY_NONE = "NONE"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_HIGH = "HIGH"


@dataclass
class StudentProfile:
    """Hồ sơ sinh viên. Toàn bộ là DEMO DATA — backend chưa có auth/profile thật."""

    student_id: str
    full_name: str
    class_name: str
    major: str
    cohort: str = ""
    email: str = ""
    is_demo: bool = True


@dataclass
class ScheduleItem:
    """1 buổi học trong thời khóa biểu. DEMO DATA — backend chưa có API lịch học."""

    item_id: str
    date: str  # ISO yyyy-mm-dd
    weekday: str
    start_time: str
    end_time: str
    subject: str
    room: str
    lecturer: str
    note: str = ""
    is_demo: bool = True


@dataclass
class TicketEvent:
    """1 mốc trong lịch sử xử lý ticket — dùng để hiển thị timeline ở trang chi tiết."""

    at: str
    actor: str
    kind: str
    note: str = ""


@dataclass
class TicketDraft:
    """Dữ liệu form trước khi tạo ticket.

    Các trường `source_*` được prefill từ lượt chat mà sinh viên bấm "Tạo yêu cầu", giúp
    nhân viên xử lý thấy ngay ngữ cảnh AI đã trả lời gì mà vẫn chưa giải quyết được.
    """

    subject: str
    category: str
    description: str
    priority: str = PRIORITY_NORMAL
    student_id: str = ""
    source_question: str = ""
    source_answer: str = ""
    source_intent: str = ""
    has_evidence: bool | None = None
    source_refs: list[str] = field(default_factory=list)
    conversation_excerpt: list[dict] = field(default_factory=list)


@dataclass
class Ticket:
    """Ticket đã tạo. `department` do routing engine quyết định, không cho user tự set."""

    ticket_id: str
    subject: str
    category: str
    department: str
    description: str
    status: str
    priority: str
    created_at: str
    updated_at: str
    student_id: str = ""
    source_question: str = ""
    source_answer: str = ""
    source_intent: str = ""
    has_evidence: bool | None = None
    source_refs: list[str] = field(default_factory=list)
    conversation_excerpt: list[dict] = field(default_factory=list)
    handover_id: str = ""
    events: list[TicketEvent] = field(default_factory=list)
    is_demo: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Ticket":
        """Dựng lại Ticket từ 1 dòng JSONL. Bỏ qua key lạ để file cũ vẫn đọc được sau khi
        schema thay đổi, và tự vá key thiếu bằng default của dataclass."""
        known = {f for f in cls.__dataclass_fields__}
        data = {k: v for k, v in raw.items() if k in known}
        data["events"] = [TicketEvent(**e) for e in raw.get("events", []) if isinstance(e, dict)]
        return cls(**data)


@dataclass
class HandoverDraft:
    """Yêu cầu chuyển sang nhân viên thật, kèm lý do máy đã đánh giá."""

    question: str
    answer_excerpt: str = ""
    reason_code: str = "user_request"
    severity: str = SEVERITY_NONE
    ticket_id: str = ""
    student_id: str = ""


@dataclass
class HandoverRequest:
    """Bản ghi handover. `eta_minutes` là ước tính DEMO, không phải SLA thật."""

    handover_id: str
    ticket_id: str
    reason_code: str
    severity: str
    status: str
    requested_at: str
    question: str = ""
    answer_excerpt: str = ""
    assigned_to: str = ""
    eta_minutes: int = 0
    student_id: str = ""
    is_demo: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "HandoverRequest":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in raw.items() if k in known})


@dataclass
class ServiceResult:
    """Bọc kết quả service theo đúng tinh thần `AskResult` của api_client: service không bao
    giờ raise ra ngoài, mọi lỗi đi vào `error` để view hiển thị error state thân thiện."""

    data: Any = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None
