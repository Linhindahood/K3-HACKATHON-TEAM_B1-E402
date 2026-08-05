"""Các hàm dựng giao diện: sidebar, chat bubble, source/media, CSS. Không gọi backend trực tiếp
(trừ check_health cho khối trạng thái hệ thống) — logic gọi RAG nằm ở api_client.py."""
from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from api_client import check_health
from config import KB_RAW_DIR, MENU_ITEMS, TAB_CAPTIONS

_NGUON_THAM_KHAO_RE = re.compile(r"\n\s*Nguồn tham khảo:\s*[\s\S]*$", re.IGNORECASE)
_CITATION_MARKER_RE = re.compile(r"\s*\[S\d+\]")

_INTENT_LABELS: dict[str, tuple[str, str]] = {
    "greeting": ("👋", "Chào bạn!"),
    "identity": ("🤖", "Trợ lý VinAI"),
    "help": ("💡", "Hướng dẫn & Dịch vụ hỗ trợ"),
    "unsupported_action": ("⚠️", "Lưu ý hướng dẫn thao tác"),
    "out_of_scope": ("ℹ️", "Phạm vi hỗ trợ"),
}
_DEFAULT_INTENT_LABEL = ("📌", "Thông tin tra cứu")

CUSTOM_CSS = """
<style>
:root { --c24-blue: #1a56db; --c24-blue-light: #eaf1fd; --c24-gray: #f4f6f9; }
section[data-testid="stSidebar"] { background-color: var(--c24-gray); }
section[data-testid="stSidebar"] .stButton button {
    border-radius: 8px; border: 1px solid #d7dee8; background: #ffffff;
}
div[data-testid="stChatMessage"] {
    border-radius: 12px; padding: 0.25rem 0.5rem; margin-bottom: 0.4rem;
}
.stButton button {
    border-radius: 10px; padding: 0.6rem 0.8rem; text-align: left;
}
div[data-testid="stExpander"] { border-radius: 10px; border: 1px solid #e2e8f0; }
h1, h2, h3 { color: var(--c24-blue); }
</style>
"""


def clean_answer(text: str) -> str:
    """Bỏ khối 'Nguồn tham khảo:' và marker [S1]/[S2].. — port từ bot/formatting.js cleanAnswer()."""
    if not text:
        return ""
    cleaned = _NGUON_THAM_KHAO_RE.sub("", text)
    cleaned = _CITATION_MARKER_RE.sub("", cleaned)
    cleaned = re.sub(r"[ \t]+\.", ".", cleaned)
    cleaned = re.sub(r"[ \t]+,", ",", cleaned)
    return cleaned.strip()


def intent_label(intent: str) -> tuple[str, str]:
    """Icon + tiêu đề hiển thị theo intent, mirror bot/formatting.js formatAnswer()."""
    return _INTENT_LABELS.get(intent, _DEFAULT_INTENT_LABEL)


def format_source_label(source: str) -> str:
    """'6_loai_phong....txt#danh-sach-phong-a113' -> nhãn dễ đọc cho expander nguồn tham khảo."""
    file_part, _, chunk_part = source.partition("#")
    file_label = re.sub(r"^\d+_", "", Path(file_part).stem).replace("_", " ").strip()
    file_label = file_label[:1].upper() + file_label[1:] if file_label else file_part
    if chunk_part:
        return f"{file_label} — {chunk_part.replace('-', ' ').strip()}"
    return file_label


def render_media_item(item: dict) -> None:
    """Hiển thị 1 media asset (ảnh bản đồ...) trả về từ backend, resolve local_path trong
    backend/knowledge_base/raw/, giống cách bot/formatting.js đính kèm ảnh cho Discord embed."""
    local_path = item.get("local_path")
    if local_path:
        image_path = KB_RAW_DIR / local_path
        if image_path.is_file():
            st.image(str(image_path), caption=item.get("title") or item.get("alt_text"))
        else:
            st.warning(f"Không tìm thấy ảnh: {local_path}")
    if item.get("url"):
        st.markdown(f"🌐 [{item.get('title', 'Xem vị trí cơ sở vật chất')}]({item['url']})")


def render_sidebar() -> str:
    """Sidebar: logo, menu, trạng thái hệ thống, nút xoá lịch sử/làm mới. Trả về tab đang chọn."""
    with st.sidebar:
        st.markdown("## 🎓 Campus 24/7")
        st.caption("Trợ lý AI dành cho sinh viên")
        st.divider()

        active_tab = st.radio("Menu", MENU_ITEMS, label_visibility="collapsed", key="active_tab")

        st.divider()
        st.markdown("**🤖 AI Assistant**")
        st.markdown("**📚 RAG Knowledge Base**")
        health = check_health()
        if health.get("ready"):
            st.markdown("🟢 System Online")
        else:
            st.markdown("🔴 System Offline")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Xóa lịch sử", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("🔄 Làm mới", use_container_width=True):
                st.rerun()

    return active_tab


def render_assistant_message(msg: dict) -> None:
    """Render 1 bubble trả lời của assistant từ session_state (dùng lại khi replay lịch sử)."""
    with st.chat_message("assistant"):
        if msg.get("error"):
            st.error(msg["error"])
            return

        icon, title = intent_label(msg.get("intent", ""))
        st.markdown(f"**{icon} {title}**")
        st.markdown(msg.get("content", "") or "_Không có nội dung trả lời._")

        if msg.get("has_evidence") is False:
            st.caption("❔ Không tìm thấy dữ liệu liên quan trong kho tri thức.")

        for item in msg.get("media") or []:
            render_media_item(item)

        sources = msg.get("sources") or []
        if sources:
            with st.expander("📚 Nguồn tham khảo"):
                for source in sources:
                    st.markdown(f"- 📄 {format_source_label(source)}")


def render_welcome_screen(questions: list[tuple[str, str]]) -> str | None:
    """Màn hình chào mừng + chip câu hỏi gợi ý. Trả về câu hỏi (không icon) nếu người dùng click."""
    st.markdown("### 👋 Xin chào! Tôi là Campus 24/7")
    st.markdown("Tôi có thể giúp bạn tra cứu quy định, học vụ và các thông tin dành cho sinh viên.")

    clicked: str | None = None
    cols = st.columns(2)
    for idx, (icon, question) in enumerate(questions):
        with cols[idx % 2]:
            if st.button(f"{icon} {question}", key=f"suggested_{idx}", use_container_width=True):
                clicked = question
    return clicked
