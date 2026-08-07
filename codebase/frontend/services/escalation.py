"""Heuristic quyết định khi nào NÊN GỢI Ý chuyển sang nhân viên thật.

⚠️ Đây là HEURISTIC phía frontend, không phải điểm tin cậy của mô hình.
Backend `/ask` hiện chỉ trả về `answer, sources, has_evidence, intent, media` — không có
confidence/grounding score nào lộ ra ngoài. Vì vậy module này chỉ suy luận từ:
  - `intent` (greeting/identity/help/unsupported_action/out_of_scope/factual)
  - `has_evidence` (câu trả lời có bám vào tài liệu hay không)
  - từ khóa nhạy cảm/khẩn cấp trong CÂU HỎI CỦA SINH VIÊN

Nguyên tắc để tránh gây hiểu nhầm:
  - Không bao giờ tự tạo ticket hay tự chuyển người thật — chỉ đề xuất, sinh viên bấm mới chạy.
  - Copy hiển thị viết dạng gợi ý, không khẳng định "AI không chắc chắn".
  - Chỉ quét từ khóa trên câu hỏi, KHÔNG quét câu trả lời (nội dung KB hay chứa chữ
    "kỷ luật", "khiếu nại"... sẽ gây báo động giả).

Module thuần Python, không import streamlit -> unit-test trực tiếp được.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from config import PROVIDER_FAILURE_MARKERS, SENSITIVE_KEYWORDS, URGENT_KEYWORDS
from services.models import SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_NONE

REASON_BACKEND_ERROR = "backend_error"
REASON_GENERATION_FAILED = "generation_failed"
REASON_UNSUPPORTED_ACTION = "unsupported_action"
REASON_URGENT_KEYWORD = "urgent_keyword"
REASON_SENSITIVE_KEYWORD = "sensitive_keyword"
REASON_NO_EVIDENCE = "no_evidence"
REASON_OUT_OF_SCOPE = "out_of_scope"
REASON_USER_REQUEST = "user_request"
REASON_NONE = ""

_MESSAGES: dict[str, str] = {
    REASON_BACKEND_ERROR: "Hệ thống đang gặp sự cố khi tra cứu. Bạn có thể gửi yêu cầu để bộ phận hỗ trợ xử lý giúp.",
    REASON_GENERATION_FAILED: "Hệ thống tìm được tài liệu liên quan nhưng chưa tạo được câu trả lời. Bạn có thể thử lại, hoặc gửi yêu cầu để bộ phận hỗ trợ trả lời trực tiếp.",
    REASON_UNSUPPORTED_ACTION: "Yêu cầu này cần thao tác thực tế mà trợ lý không tự thực hiện được. Bạn có thể tạo yêu cầu hỗ trợ để bộ phận phụ trách xử lý.",
    REASON_URGENT_KEYWORD: "Có vẻ đây là việc gấp. Nếu cần, bạn có thể chuyển ngay cho nhân viên hỗ trợ.",
    REASON_SENSITIVE_KEYWORD: "Đây có thể là vấn đề cần người phụ trách xem xét trực tiếp. Nếu muốn, bạn có thể chuyển cho nhân viên hỗ trợ.",
    REASON_NO_EVIDENCE: "Mình chưa tìm thấy thông tin chính thức cho câu hỏi này trong kho tri thức. Bạn có thể tạo yêu cầu để bộ phận phụ trách kiểm tra.",
    REASON_OUT_OF_SCOPE: "Câu hỏi này nằm ngoài phạm vi dữ liệu của chương trình. Nếu cần, bạn có thể liên hệ nhân viên hỗ trợ.",
    REASON_USER_REQUEST: "Bạn đã yêu cầu gặp nhân viên hỗ trợ.",
}

# Gợi ý category ticket theo lý do — view dùng làm giá trị mặc định của selectbox.
_CATEGORY_BY_REASON: dict[str, str] = {
    REASON_GENERATION_FAILED: "ky_thuat",
    REASON_UNSUPPORTED_ACTION: "dich_vu",
    REASON_URGENT_KEYWORD: "khac",
    REASON_SENSITIVE_KEYWORD: "noi_quy",
    REASON_NO_EVIDENCE: "hoc_vu",
    REASON_OUT_OF_SCOPE: "khac",
    REASON_BACKEND_ERROR: "ky_thuat",
}


@dataclass(frozen=True)
class Escalation:
    """Kết quả đánh giá 1 lượt trả lời."""

    severity: str = SEVERITY_NONE
    reason_code: str = REASON_NONE
    message: str = ""

    @property
    def should_offer(self) -> bool:
        """Có hiển thị banner gợi ý handover hay không."""
        return self.severity != SEVERITY_NONE

    @property
    def suggested_category(self) -> str:
        return _CATEGORY_BY_REASON.get(self.reason_code, "khac")


def _normalize(text: str) -> str:
    """Chuẩn hóa NFC + lowercase. Giữ nguyên dấu tiếng Việt vì dấu chính là thứ phân biệt
    'kỷ luật' với 'kỹ thuật' — bỏ dấu sẽ làm tăng báo động giả."""
    return unicodedata.normalize("NFC", text or "").lower()


def _contains_keyword(text: str, keywords: tuple[str, ...]) -> str:
    """Trả về từ khóa khớp đầu tiên, hoặc "" nếu không khớp.

    Dùng ranh giới từ (`\\b`) thay vì substring thô để 'gấp' không khớp nhầm trong 'gấp đôi'
    hay 'cấp' trong 'cấp bậc'.
    """
    haystack = _normalize(text)
    for keyword in keywords:
        pattern = r"(?<!\w)" + re.escape(_normalize(keyword)) + r"(?!\w)"
        if re.search(pattern, haystack):
            return keyword
    return ""


def _looks_like_generation_failure(answer: str) -> bool:
    """Nhận diện câu trả lời fallback khi provider LLM lỗi.

    Khớp theo chuỗi con vì backend trả về hằng số cố định (PROVIDER_FAILURE_ANSWER). Chấp nhận
    rủi ro khớp nhầm rất thấp: các cụm này không xuất hiện trong tài liệu kho tri thức.
    """
    haystack = _normalize(answer)
    return any(_normalize(marker) in haystack for marker in PROVIDER_FAILURE_MARKERS)


def assess(
    question: str,
    *,
    intent: str = "",
    has_evidence: bool | None = None,
    error: str | None = None,
    answer: str = "",
) -> Escalation:
    """Đánh giá mức độ nên đề xuất handover cho 1 lượt hỏi–đáp.

    Thứ tự ưu tiên: lỗi hệ thống > LLM không sinh được câu trả lời > khẩn cấp > nhạy cảm >
    không hỗ trợ thao tác > thiếu bằng chứng > ngoài phạm vi.
    """
    if error:
        return _build(SEVERITY_HIGH, REASON_BACKEND_ERROR)

    # Backend tìm ra tài liệu nhưng LLM fail: has_evidence=True nên các nhánh dưới sẽ bỏ qua,
    # trong khi sinh viên không nhận được thông tin gì -> phải bắt riêng ở đây.
    if _looks_like_generation_failure(answer):
        return _build(SEVERITY_HIGH, REASON_GENERATION_FAILED)

    grounded = intent == "factual" and bool(has_evidence)

    if _contains_keyword(question, URGENT_KEYWORDS):
        return _build(SEVERITY_HIGH, REASON_URGENT_KEYWORD)

    if _contains_keyword(question, SENSITIVE_KEYWORDS):
        # Hạ xuống MEDIUM khi câu trả lời đã có nguồn: "quy định kỷ luật là gì?" là câu hỏi
        # tra cứu thông tin bình thường, không phải ca kỷ luật cá nhân cần người xử lý.
        severity = SEVERITY_MEDIUM if grounded else SEVERITY_HIGH
        return _build(severity, REASON_SENSITIVE_KEYWORD)

    if intent == "unsupported_action":
        return _build(SEVERITY_HIGH, REASON_UNSUPPORTED_ACTION)

    if intent == "out_of_scope":
        return _build(SEVERITY_MEDIUM, REASON_OUT_OF_SCOPE)

    if intent == "factual" and has_evidence is False:
        return _build(SEVERITY_MEDIUM, REASON_NO_EVIDENCE)

    return Escalation()


def _build(severity: str, reason_code: str) -> Escalation:
    return Escalation(severity=severity, reason_code=reason_code, message=_MESSAGES.get(reason_code, ""))


def user_requested() -> Escalation:
    """Sinh viên chủ động bấm 'Gặp nhân viên hỗ trợ' — luôn hợp lệ bất kể heuristic nói gì."""
    return _build(SEVERITY_HIGH, REASON_USER_REQUEST)
