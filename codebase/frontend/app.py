"""Streamlit — Campus 24/7, giao diện demo cho team.

Gọi cùng backend FastAPI (POST /ask, GET /health) mà Discord bot dùng — không tự chứa logic RAG.
Các phần ticket/lịch học/handover/hồ sơ hiện chạy trên service mock (xem services/factory.py),
đổi sang API thật chỉ cần đặt USE_MOCK_SERVICES=0.

Chạy: streamlit run frontend/app.py
"""
from __future__ import annotations

import streamlit as st

from config import (
    ABOUT_TEXT,
    APP_SUBTITLE,
    APP_TITLE,
    NAV_ABOUT,
    NAV_CHAT,
    NAV_FAQ,
    NAV_PROFILE,
    NAV_SCHEDULE,
    NAV_TICKETS,
)
from services.factory import get_services
from ui import CUSTOM_CSS, render_sidebar
from views import chat_view, faq_view, profile_view, schedule_view, tickets_view

# Giữ tên cũ để code/test đang import từ app.py không gãy sau khi tách view.
from views.chat_view import handle_user_turn, render_chat_history  # noqa: F401


def init_session_state() -> None:
    """Khởi tạo state dùng chung. Giữ nguyên khi Streamlit rerun trong cùng session."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = True
    if "profile" not in st.session_state:
        result = get_services().profile.get_profile()
        st.session_state.profile = result.data if result.ok else None


def _apply_pending_nav() -> None:
    """Áp yêu cầu chuyển trang do các view đặt ở lần chạy trước.

    Phải chạy TRƯỚC render_sidebar(): sau khi widget radio `nav` được khởi tạo thì Streamlit
    không cho phép ghi đè st.session_state['nav'] nữa (sẽ raise).
    """
    target = st.session_state.pop("_nav_request", None)
    if target:
        st.session_state["nav"] = target


_VIEWS = {
    NAV_CHAT: chat_view.render,
    NAV_SCHEDULE: schedule_view.render,
    NAV_TICKETS: tickets_view.render,
    NAV_FAQ: faq_view.render,
    NAV_PROFILE: profile_view.render,
}


def main() -> None:
    st.set_page_config(page_title="Campus 24/7", page_icon="🎓", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    init_session_state()
    _apply_pending_nav()

    active_page = render_sidebar()

    st.markdown(f"# {APP_TITLE}")
    st.caption(APP_SUBTITLE)

    if active_page == NAV_ABOUT:
        st.markdown(ABOUT_TEXT)
        return

    _VIEWS.get(active_page, chat_view.render)()


if __name__ == "__main__":
    main()
