"""Trang Hồ sơ — thông tin sinh viên demo + đăng xuất.

⚠️ DEMO: backend chưa có auth/SSO. Hồ sơ ở đây là dữ liệu giả cố định, "đăng xuất" chỉ xóa
state phía client chứ không có phiên đăng nhập thật để hủy.
"""
from __future__ import annotations

import streamlit as st

from services.factory import get_services
from ui import demo_banner, render_empty_state


def _render_logged_out() -> None:
    render_empty_state("🔒", "Bạn đã đăng xuất", "Đăng nhập lại để xem hồ sơ và các yêu cầu hỗ trợ của bạn.")
    if st.button("🔑 Đăng nhập lại (demo)", key="profile_login", use_container_width=True):
        result = get_services().profile.get_profile()
        st.session_state["profile"] = result.data if result.ok else None
        st.session_state["logged_in"] = True
        st.rerun()


def render() -> None:
    st.caption("Thông tin sinh viên và phiên đăng nhập hiện tại.")

    if not st.session_state.get("logged_in", True):
        _render_logged_out()
        return

    profile = st.session_state.get("profile")
    if profile is None:
        st.error("❌ Không tải được hồ sơ sinh viên.")
        return

    demo_banner("Hồ sơ sinh viên minh họa, không phải tài khoản thật")

    st.markdown(
        f'<div class="c24-card">'
        f'<div class="c24-card-title">👤 {profile.full_name}</div>'
        f'<span class="c24-badge c24-badge-blue">🆔 {profile.student_id}</span>'
        f'<span class="c24-badge c24-badge-gray">🏫 {profile.class_name}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Ngành học**")
        st.markdown(profile.major or "—")
        st.markdown("**Khóa**")
        st.markdown(profile.cohort or "—")
    with col2:
        st.markdown("**Email**")
        st.markdown(profile.email or "—")
        st.markdown("**Trạng thái**")
        st.markdown("🟢 Đang học")

    st.divider()

    # Thống kê nhanh lấy từ service ticket, không hard-code.
    result = get_services().tickets.list_tickets(student_id=profile.student_id)
    if result.ok:
        tickets = result.data
        open_count = sum(1 for t in tickets if t.status in {"OPEN", "IN_PROGRESS", "WAITING"})
        col_a, col_b = st.columns(2)
        col_a.metric("Tổng yêu cầu đã gửi", len(tickets))
        col_b.metric("Đang chờ xử lý", open_count)

    st.divider()
    if st.button("🚪 Đăng xuất", key="profile_logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["profile"] = None
        st.rerun()
