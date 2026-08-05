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

APP_TITLE = "🎓 Campus 24/7"
APP_SUBTITLE = "Trợ lý AI dành cho sinh viên"

TAB_CHAT = "💬 Chat"
TAB_REGULATIONS = "📚 Quy định sinh viên"
TAB_LOOKUP = "🔎 Tra cứu"
TAB_ABOUT = "ℹ️ Giới thiệu"
MENU_ITEMS = [TAB_CHAT, TAB_REGULATIONS, TAB_LOOKUP, TAB_ABOUT]

# Câu hỏi gợi ý grounded theo file thật trong backend/knowledge_base/raw/
# (icon, câu hỏi) — icon chỉ dùng để hiển thị nút, câu hỏi gửi đi không kèm icon.
_Q_NOI_QUY = ("📋", "Nội quy chung của sinh viên là gì?")
_Q_DIEM_DANH = ("📅", "Quy định về điểm danh và nghỉ học như thế nào?")
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
