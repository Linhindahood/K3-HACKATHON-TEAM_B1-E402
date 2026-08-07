"""Trang FAQ & Tra cứu — duyệt kho tri thức THẬT đã ingest.

Khác với các trang demo khác, dữ liệu ở đây là thật: đọc từ
backend/knowledge_base/processed/chunks.jsonl, gom nhóm theo heading gốc của tài liệu và
kèm link nguồn để sinh viên đối chiếu.
"""
from __future__ import annotations

import streamlit as st

from config import NAV_CHAT
from services import knowledge
from ui import render_empty_state, request_nav


def _render_entry(entry: knowledge.KBEntry, idx: int) -> None:
    """1 mục kiến thức: tiêu đề mở rộng được, nội dung, nguồn, và nút hỏi sâu thêm trong Chat."""
    with st.expander(entry.title):
        st.markdown(entry.text)
        if entry.source_url:
            st.markdown(f'<div class="c24-meta">📄 Nguồn: <a href="{entry.source_url}" target="_blank">{entry.source}</a></div>', unsafe_allow_html=True)
        elif entry.source:
            st.markdown(f'<div class="c24-meta">📄 Nguồn: {entry.source}</div>', unsafe_allow_html=True)

        if st.button("💬 Hỏi thêm về mục này", key=f"faq_ask_{idx}", use_container_width=True):
            st.session_state["pending_question"] = entry.title
            request_nav(NAV_CHAT)


def render() -> None:
    st.caption("Tra cứu câu hỏi thường gặp, quy định và dịch vụ — trích từ tài liệu chính thức của chương trình.")

    if not knowledge.is_available():
        render_empty_state(
            "📚",
            "Kho tri thức chưa sẵn sàng",
            "Chưa tìm thấy chunks.jsonl. Chạy ingest để tạo: `python -m backend.rag.ingest` trong thư mục codebase/.",
        )
        return

    groups = knowledge.list_groups()
    group_names = ["Tất cả"] + [name for name, _ in groups]

    col1, col2 = st.columns([2, 3])
    with col1:
        chosen = st.selectbox("Danh mục", group_names, key="faq_group")
    with col2:
        query = st.text_input("Tìm kiếm", key="faq_query", placeholder="VD: điểm danh, bảo lưu, thư viện...")

    entries = knowledge.get_entries(group=None if chosen == "Tất cả" else chosen, query=query)

    if not entries:
        render_empty_state("🔍", "Không tìm thấy kết quả", "Thử từ khóa khác, hoặc hỏi trực tiếp trợ lý ở trang Chat.")
        return

    st.caption(f"{len(entries)} mục")
    for idx, entry in enumerate(entries):
        _render_entry(entry, idx)
