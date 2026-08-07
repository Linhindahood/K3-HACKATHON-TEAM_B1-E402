"""Cấu hình chung cho Streamlit UI: env, đường dẫn, hằng số nội dung."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

FRONTEND_DIR = Path(__file__).resolve().parent
CODEBASE_DIR = FRONTEND_DIR.parent

load_dotenv(dotenv_path=CODEBASE_DIR / ".env")

BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
KB_RAW_DIR: Path = CODEBASE_DIR / "backend" / "knowledge_base" / "raw"
REQUEST_TIMEOUT_S: float = 30.0
HEALTH_TIMEOUT_S: float = 5.0

# Kho tri thức đã ingest — nguồn dữ liệu THẬT cho trang FAQ/Tra cứu.
# File này gitignored + tự sinh bởi backend/rag/ingest.py, có thể chưa tồn tại sau khi clone
# -> services/knowledge.py phải xử lý trường hợp thiếu file bằng empty state, không được crash.
KB_CHUNKS_PATH: Path = CODEBASE_DIR / "backend" / "knowledge_base" / "processed" / "chunks.jsonl"

# Backend hiện chỉ có POST /ask + GET /health. Ticket/lịch học/handover/hồ sơ chưa có API thật
# nên mặc định chạy mock. Khi backend bổ sung endpoint, chỉ cần đặt USE_MOCK_SERVICES=0 —
# không phải sửa bất kỳ view nào.
USE_MOCK_SERVICES: bool = os.getenv("USE_MOCK_SERVICES", "1").strip().lower() not in {"0", "false", "no"}

_DEFAULT_LOCAL_STORE = FRONTEND_DIR / ".local_store"


def local_store_dir() -> Path:
    """Thư mục lưu ticket/handover của bản mock.

    Là *hàm* chứ không phải hằng số import-time để test có thể trỏ sang tmp_path qua biến môi
    trường mà không cần reload module. Rule `*.jsonl` trong codebase/.gitignore đã tự động
    loại các file sinh ra ở đây khỏi git.
    """
    override = os.getenv("CAMPUS247_LOCAL_STORE")
    return Path(override) if override else _DEFAULT_LOCAL_STORE

APP_TITLE = "🎓 Campus 24/7"
APP_SUBTITLE = "Trợ lý AI dành cho sinh viên"

TAB_CHAT = "💬 Chat"
TAB_REGULATIONS = "📚 Quy định sinh viên"
TAB_LOOKUP = "🔎 Tra cứu"
TAB_ABOUT = "ℹ️ Giới thiệu"
MENU_ITEMS = [TAB_CHAT, TAB_REGULATIONS, TAB_LOOKUP, TAB_ABOUT]
# Chip danh mục hiển thị ở màn hình chào mừng (loại bỏ tab Giới thiệu) — mirror mockup "Mình có
# thể hỗ trợ bạn về: [..] [..]" ở docs, chỉ giữ danh mục thực sự có dữ liệu/tool hỗ trợ.
CATEGORY_TABS = [TAB_CHAT, TAB_REGULATIONS, TAB_LOOKUP]

# Câu hỏi gợi ý grounded theo file thật trong backend/knowledge_base/raw/
# (icon, câu hỏi) — icon chỉ dùng để hiển thị nút, câu hỏi gửi đi không kèm icon.
#
# ⚠️ Câu gợi ý PHẢI dùng đúng từ vựng của tài liệu, nếu không retriever lấy nhầm đoạn và LLM
# trả về __INSUFFICIENT_CONTEXT__ (hiện ra "chưa tìm thấy thông tin"). Ví dụ: tài liệu dùng
# "chuyên cần", không dùng "điểm danh" — hỏi "điểm danh" sẽ không ra kết quả.
_Q_NOI_QUY = ("📋", "Nội quy chung của sinh viên là gì?")
_Q_DIEM_DANH = ("📅", "Quy định chuyên cần như thế nào? Được nghỉ tối đa bao nhiêu buổi?")
_Q_BAO_LUU = ("🏫", "Thủ tục bảo lưu kết quả học tập ra sao?")
_Q_PHONG = ("🚪", "Có những loại phòng nào và cách đặt phòng ra sao?")
_Q_BAN_DO = ("🗺️", "Cơ sở vật chất của trường ở đâu? Cho tôi xem bản đồ.")
_Q_TIEN_ICH = ("🛠️", "Trường có những tiện ích gì cho sinh viên?")

SUGGESTED_QUESTIONS: dict[str, list[tuple[str, str]]] = {
    TAB_CHAT: [_Q_NOI_QUY, _Q_DIEM_DANH, _Q_BAO_LUU, _Q_PHONG, _Q_BAN_DO, _Q_TIEN_ICH],
    TAB_REGULATIONS: [_Q_NOI_QUY, _Q_DIEM_DANH, _Q_BAO_LUU],
    TAB_LOOKUP: [_Q_PHONG, _Q_BAN_DO, _Q_TIEN_ICH],
}

TAB_CAPTIONS: dict[str, str] = {
    TAB_CHAT: "Hỏi bất kỳ điều gì về nội quy, học vụ và tiện ích dành cho sinh viên.",
    TAB_REGULATIONS: "Tra cứu nội quy, điểm danh, nghỉ học, bảo lưu kết quả học tập.",
    TAB_LOOKUP: "Tra cứu phòng ốc, tiện ích và vị trí cơ sở vật chất.",
}

# --- Điều hướng sidebar (trang chính) --------------------------------------
NAV_CHAT = "💬 Chat"
NAV_SCHEDULE = "📅 Lịch học"
NAV_TICKETS = "🎫 Yêu cầu của tôi"
NAV_FAQ = "❓ FAQ & Tra cứu"
NAV_PROFILE = "👤 Hồ sơ"
NAV_ABOUT = "ℹ️ Giới thiệu"
NAV_ITEMS = [NAV_CHAT, NAV_SCHEDULE, NAV_TICKETS, NAV_FAQ, NAV_PROFILE, NAV_ABOUT]

# Quick action ở màn hình chat. `question` -> bơm câu hỏi vào chat; `nav` -> nhảy sang trang.
# Tách data khỏi logic để thêm/bớt nút không phải sửa view.
QUICK_ACTIONS: list[dict] = [
    {"label": "📚 Học vụ", "kind": "question", "value": "Cấu trúc chương trình học gồm những gì?"},
    {"label": "📜 Nội quy & quy định", "kind": "question", "value": "Quy định đào tạo và nội quy học tập như thế nào?"},
    {"label": "📅 Lịch học", "kind": "nav", "value": NAV_SCHEDULE},
    {"label": "📝 Dịch vụ sinh viên", "kind": "question", "value": "Trường có những dịch vụ tiện ích gì cho sinh viên?"},
    {"label": "🎫 Yêu cầu hỗ trợ", "kind": "nav", "value": NAV_TICKETS},
    {"label": "👨‍💼 Gặp nhân viên", "kind": "handover", "value": ""},
]

# --- Ticket: routing & phân loại -------------------------------------------
# Không cho user tự truyền department — luôn suy ra từ category qua bảng này (business rule).
TICKET_CATEGORIES: list[tuple[str, str]] = [
    ("hoc_vu", "Học vụ / Đào tạo"),
    ("lich_hoc", "Lịch học / Lịch thi"),
    ("noi_quy", "Nội quy & quy định"),
    ("co_so_vat_chat", "Phòng học & cơ sở vật chất"),
    ("dich_vu", "Dịch vụ sinh viên"),
    ("ky_thuat", "Tài khoản & kỹ thuật"),
    ("khac", "Khác"),
]

DEPARTMENT_BY_CATEGORY: dict[str, str] = {
    "hoc_vu": "Phòng Đào tạo",
    "lich_hoc": "Phòng Đào tạo",
    "noi_quy": "Phòng Công tác Sinh viên",
    "co_so_vat_chat": "Thư viện & Cơ sở vật chất",
    "dich_vu": "Phòng Dịch vụ Sinh viên",
    "ky_thuat": "Phòng CNTT",
    "khac": "Trung tâm Hỗ trợ Sinh viên",
}
DEFAULT_DEPARTMENT = "Trung tâm Hỗ trợ Sinh viên"

# --- Handover: từ khóa nhận diện ca nhạy cảm / khẩn cấp ---------------------
# Để ở config để chỉnh ngưỡng nhận diện mà không phải sửa logic trong services/escalation.py.
# Lưu ý: đây chỉ là HEURISTIC hỗ trợ, không phải phán quyết — UI luôn hiển thị dạng gợi ý.
SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "khiếu nại", "tố cáo", "kỷ luật", "đình chỉ", "buộc thôi học",
    "quấy rối", "bạo lực", "trầm cảm", "tai nạn", "phản ánh",
)
URGENT_KEYWORDS: tuple[str, ...] = (
    "khẩn cấp", "gấp", "ngay lập tức", "cấp cứu", "hạn chót hôm nay", "sắp hết hạn",
)

# Dấu hiệu backend tìm được tài liệu nhưng LLM không sinh được câu trả lời
# (backend/rag/response_policy.py :: PROVIDER_FAILURE_ANSWER). Trường hợp này `has_evidence`
# vẫn là True nên heuristic thường sẽ bỏ qua, trong khi sinh viên thực tế không nhận được gì
# hữu ích -> phải chủ động đề nghị hỗ trợ.
# ⚠️ Đây là chuỗi khớp với hằng số bên backend: nếu backend đổi câu chữ, cập nhật ở đây.
PROVIDER_FAILURE_MARKERS: tuple[str, ...] = (
    "chưa thể tạo câu trả lời",
)

ABOUT_TEXT = """
**Campus 24/7** là chatbot hỗ trợ sinh viên VinAI tra cứu nội quy, tiện ích và vị trí cơ sở vật
chất, dùng kỹ thuật RAG (Retrieval-Augmented Generation) trên kho tri thức nội bộ của chương trình.

- Câu trả lời được sinh ra dựa trên tài liệu thật (nội quy, sổ tay chương trình, hướng dẫn đặt
  phòng, vị trí cơ sở vật chất) — kèm nguồn tham khảo để đối chiếu.
- Đây là **giao diện debug/demo nội bộ** (Streamlit), sản phẩm chính thức cho sinh viên là
  **Discord bot**. Cả hai đều gọi chung một backend RAG qua `POST /ask`.
- ⚠️ Bot **không tự thực hiện đặt lịch/đặt phòng thật** — chỉ trả lời bằng text hướng dẫn quy
  trình, sinh viên vẫn cần làm theo hướng dẫn để đặt phòng chính thức.
"""
