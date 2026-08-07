"""Các hàm dựng giao diện: sidebar, chat bubble, source/media, CSS. Không gọi backend trực tiếp
(trừ check_health cho khối trạng thái hệ thống) — logic gọi RAG nằm ở api_client.py."""
from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from api_client import check_health
from config import CATEGORY_TABS, KB_RAW_DIR, MENU_ITEMS, NAV_ITEMS, TAB_CAPTIONS

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

# Màu badge theo intent — giúp phân biệt nhanh loại câu trả lời (thông tin/tra cứu vs cảnh báo
# phạm vi/thao tác) mà không cần đọc hết nội dung, mirror mức độ "cần chú ý" của từng intent.
_INTENT_COLORS: dict[str, str] = {
    "help": "green",
    "unsupported_action": "amber",
    "out_of_scope": "amber",
}
_DEFAULT_INTENT_COLOR = "blue"

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
.c24-badge {
    display: inline-block; padding: 0.15rem 0.65rem; border-radius: 999px;
    font-size: 0.82rem; font-weight: 600; margin: 0 0.35rem 0.35rem 0;
}
.c24-badge-blue  { background: #eaf1fd; color: #1a56db; }
.c24-badge-green { background: #e6f4ea; color: #1e7e34; }
.c24-badge-amber { background: #fff4e5; color: #b26a00; }
.c24-badge-red   { background: #fdecea; color: #b3261e; }
.c24-badge-gray  { background: #eceff3; color: #4a5568; }
.c24-chip-row .stButton button { border-radius: 999px; font-weight: 600; }
.c24-card {
    border: 1px solid #e2e8f0; border-radius: 12px; padding: 0.9rem 1.1rem;
    margin-bottom: 0.7rem; background: #ffffff;
}
.c24-card-title { font-weight: 700; color: #1a2b4b; margin-bottom: 0.3rem; }
.c24-meta { color: #5b6b82; font-size: 0.85rem; }
.c24-notice {
    border-radius: 10px; padding: 0.7rem 0.9rem; margin: 0.4rem 0 0.6rem 0;
    border-left: 4px solid; font-size: 0.92rem;
}
.c24-notice-high   { background: #fdecea; border-color: #d93025; color: #7f1d1b; }
.c24-notice-medium { background: #fff4e5; border-color: #f59e0b; color: #7a4a00; }
.c24-demo {
    background: #f4f6f9; border: 1px dashed #b9c3d1; border-radius: 8px;
    padding: 0.45rem 0.75rem; margin-bottom: 0.8rem;
    color: #4a5568; font-size: 0.85rem;
}
/* Responsive: trên màn hẹp cho các cột xuống hàng thay vì bóp chữ */
@media (max-width: 640px) {
    .c24-badge { font-size: 0.75rem; }
    .c24-card { padding: 0.7rem 0.8rem; }
}
</style>
"""

# Màu badge theo trạng thái ticket — đỏ/cam cho việc còn treo, xanh cho đã xong, xám cho đóng.
_STATUS_STYLES: dict[str, tuple[str, str]] = {
    "OPEN": ("red", "🔴 Mới tạo"),
    "IN_PROGRESS": ("blue", "🔧 Đang xử lý"),
    "WAITING": ("amber", "⏳ Chờ phản hồi"),
    "RESOLVED": ("green", "✅ Đã giải quyết"),
    "CLOSED": ("gray", "🔒 Đã đóng"),
}

_PRIORITY_STYLES: dict[str, tuple[str, str]] = {
    "LOW": ("gray", "Thấp"),
    "NORMAL": ("blue", "Bình thường"),
    "HIGH": ("amber", "Cao"),
    "URGENT": ("red", "Khẩn cấp"),
}


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


def intent_badge_html(intent: str) -> str:
    """Badge màu cho intent — xanh dương mặc định, xanh lá cho help, cam cho các câu trả lời
    cần sinh viên lưu ý (ngoài phạm vi / không hỗ trợ thao tác)."""
    icon, title = intent_label(intent)
    color = _INTENT_COLORS.get(intent, _DEFAULT_INTENT_COLOR)
    return f'<span class="c24-badge c24-badge-{color}">{icon} {title}</span>'


def evidence_badge_html(has_evidence: bool | None) -> str:
    """Badge cho biết câu trả lời có nguồn xác thực trong kho tri thức hay không."""
    if has_evidence:
        return '<span class="c24-badge c24-badge-green">✅ Có nguồn xác thực</span>'
    return '<span class="c24-badge c24-badge-amber">❔ Chưa tìm thấy nguồn xác thực</span>'


def status_pill_html(status: str) -> str:
    """Badge trạng thái ticket."""
    color, label = _STATUS_STYLES.get(status, ("gray", status))
    return f'<span class="c24-badge c24-badge-{color}">{label}</span>'


def priority_pill_html(priority: str) -> str:
    """Badge mức độ ưu tiên ticket."""
    color, label = _PRIORITY_STYLES.get(priority, ("gray", priority))
    return f'<span class="c24-badge c24-badge-{color}">Ưu tiên: {label}</span>'


def severity_notice_html(severity: str, message: str) -> str:
    """Khối thông báo gợi ý chuyển nhân viên hỗ trợ.

    Cố ý viết dạng đề xuất chứ không phải phán quyết — đây chỉ là heuristic phía frontend
    (backend không trả về confidence score), nên không được khẳng định "AI không chắc chắn".
    """
    tone = "high" if severity == "HIGH" else "medium"
    icon = "🚨" if severity == "HIGH" else "💡"
    return f'<div class="c24-notice c24-notice-{tone}">{icon} {message}</div>'


def demo_banner(text: str = "Dữ liệu minh họa") -> None:
    """Nhãn DEMO DATA. Bắt buộc ở các trang dùng dữ liệu bịa (lịch học, hồ sơ, ticket) để
    sinh viên không nhầm là dữ liệu thật của trường."""
    st.markdown(
        f'<div class="c24-demo">🧪 <b>DEMO DATA</b> — {text}. '
        "Backend hiện chưa có API thật cho phần này.</div>",
        unsafe_allow_html=True,
    )


def render_empty_state(icon: str, title: str, hint: str = "") -> None:
    """Empty state thống nhất cho mọi trang."""
    st.markdown(f"### {icon} {title}")
    if hint:
        st.caption(hint)


def request_nav(target: str) -> None:
    """Đặt yêu cầu chuyển trang rồi rerun.

    KHÔNG ghi thẳng st.session_state['nav'] vì widget radio đã được khởi tạo trong lần chạy
    này — Streamlit sẽ raise. Thay vào đó ghi vào khóa trung gian, app.py pop ra TRƯỚC khi
    dựng sidebar ở lần chạy kế tiếp.
    """
    st.session_state["_nav_request"] = target
    st.rerun()


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
    """Sidebar: logo, điều hướng trang, hồ sơ rút gọn, trạng thái hệ thống. Trả về trang đang chọn."""
    with st.sidebar:
        st.markdown("## 🎓 Campus 24/7")
        st.caption("Trợ lý AI dành cho sinh viên")
        st.divider()

        nav = st.radio("Điều hướng", NAV_ITEMS, label_visibility="collapsed", key="nav")

        st.divider()
        profile = st.session_state.get("profile")
        if profile is not None and st.session_state.get("logged_in", True):
            st.markdown(f"**👤 {profile.full_name}**")
            st.caption(f"{profile.student_id} · {profile.class_name}")
        else:
            st.caption("👤 Chưa đăng nhập")

        st.divider()
        health = check_health()
        st.markdown("🟢 System Online" if health.get("ready") else "🔴 System Offline")
        st.caption("🤖 AI Assistant · 📚 RAG Knowledge Base")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Xóa lịch sử", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("🔄 Làm mới", use_container_width=True):
                st.rerun()

    return nav


def render_assistant_message(msg: dict, idx: int | None = None) -> None:
    """Render 1 bubble trả lời của assistant từ session_state (dùng lại khi replay lịch sử).

    `idx` là vị trí message trong lịch sử, dùng làm hậu tố key cho các nút hành động. Bỏ trống
    (mặc định) thì không vẽ nút — giữ nguyên hành vi cũ cho mọi lời gọi không truyền idx.
    """
    with st.chat_message("assistant"):
        if msg.get("error"):
            st.error(msg["error"])
            if idx is not None:
                render_message_actions(msg, idx)
            return

        badges = intent_badge_html(msg.get("intent", ""))
        if msg.get("has_evidence") is not None:
            badges += evidence_badge_html(msg.get("has_evidence"))
        st.markdown(badges, unsafe_allow_html=True)

        st.markdown(msg.get("content", "") or "_Không có nội dung trả lời._")

        for item in msg.get("media") or []:
            render_media_item(item)

        sources = msg.get("sources") or []
        if sources:
            with st.expander(f"📚 Nguồn tham khảo ({len(sources)})"):
                for source in sources:
                    st.markdown(f"- 📄 {format_source_label(source)}")

        if idx is not None:
            escalation = msg.get("escalation") or {}
            if escalation.get("message"):
                st.markdown(
                    severity_notice_html(escalation.get("severity", ""), escalation["message"]),
                    unsafe_allow_html=True,
                )
            render_message_actions(msg, idx)


def render_message_actions(msg: dict, idx: int) -> None:
    """Hai hành động tiếp theo cho 1 câu trả lời: tạo yêu cầu hỗ trợ / gặp nhân viên.

    Key có hậu tố idx để tránh DuplicateWidgetID khi lịch sử có nhiều lượt. Lịch sử chỉ được
    append nên idx ổn định qua các lần rerun.
    """
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎫 Tạo yêu cầu hỗ trợ", key=f"tk_create_{idx}", use_container_width=True):
            st.session_state["ticket_draft"] = _draft_from_message(msg)
            request_nav(NAV_ITEMS[2])  # 🎫 Yêu cầu của tôi
    with col2:
        if st.button("👨‍💼 Gặp nhân viên hỗ trợ", key=f"tk_handover_{idx}", use_container_width=True):
            st.session_state["handover_ctx"] = _draft_from_message(msg)
            request_nav(NAV_ITEMS[2])


def _draft_from_message(msg: dict) -> dict:
    """Gom ngữ cảnh hội thoại để prefill form ticket/handover.

    Mang theo cả câu hỏi gốc, câu trả lời AI, intent và nguồn — nhân viên xử lý cần thấy AI
    đã trả lời gì mà vẫn chưa giải quyết được, thay vì phải hỏi lại sinh viên từ đầu.
    """
    messages: list[dict] = st.session_state.get("messages", [])
    question = ""
    for item in reversed(messages):
        if item.get("role") == "user":
            question = item.get("content", "")
            break

    return {
        "question": question,
        "answer": msg.get("content", ""),
        "intent": msg.get("intent", ""),
        "has_evidence": msg.get("has_evidence"),
        "sources": list(msg.get("sources") or []),
        "escalation": msg.get("escalation") or {},
        "excerpt": messages[-6:],
    }


def render_welcome_screen(active_tab: str, questions: list[tuple[str, str]]) -> str | None:
    """Màn hình chào mừng: chip danh mục (chọn nhanh chủ đề, giống mockup "Mình có thể hỗ trợ bạn
    về: [..] [..]") + câu hỏi gợi ý theo danh mục đang chọn. Trả về câu hỏi (không icon) nếu
    người dùng click một câu hỏi gợi ý."""
    st.markdown("### 👋 Xin chào! Tôi là Campus 24/7")
    st.markdown("Mình có thể hỗ trợ bạn về:")

    st.markdown('<div class="c24-chip-row">', unsafe_allow_html=True)
    cat_cols = st.columns(len(CATEGORY_TABS))
    for idx, tab in enumerate(CATEGORY_TABS):
        with cat_cols[idx]:
            is_active = tab == active_tab
            if st.button(
                tab,
                key=f"category_{idx}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ) and not is_active:
                st.session_state.active_tab = tab
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    clicked: str | None = None
    cols = st.columns(2)
    for idx, (icon, question) in enumerate(questions):
        with cols[idx % 2]:
            if st.button(f"{icon} {question}", key=f"suggested_{idx}", use_container_width=True):
                clicked = question
    return clicked
