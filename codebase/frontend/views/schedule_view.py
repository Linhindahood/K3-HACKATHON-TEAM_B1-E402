"""Trang Lịch học — xem theo ngày / theo tuần.

⚠️ Toàn bộ dữ liệu là DEMO: backend không có API lịch học và kho tri thức cũng không chứa
thời khóa biểu cá nhân của từng sinh viên. Trang này minh họa luồng "dữ liệu động thì query
database/API, không nhét vào vector store".
"""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from services.factory import get_services
from ui import demo_banner, render_empty_state

_MODE_DAY = "Theo ngày"
_MODE_WEEK = "Theo tuần"


def _range_for(mode: str, anchor: date) -> tuple[date, date]:
    """Khoảng ngày cần lấy. Tuần bắt đầu từ Thứ Hai theo thói quen lịch học VN."""
    if mode == _MODE_DAY:
        return anchor, anchor
    monday = anchor - timedelta(days=anchor.weekday())
    return monday, monday + timedelta(days=6)


def _render_item(item) -> None:
    st.markdown(
        f'<div class="c24-card">'
        f'<div class="c24-card-title">🕘 {item.start_time}–{item.end_time} · {item.subject}</div>'
        f'<span class="c24-badge c24-badge-blue">🚪 Phòng {item.room}</span>'
        f'<span class="c24-badge c24-badge-gray">👨‍🏫 {item.lecturer}</span>'
        f'<div class="c24-meta">{item.weekday}, {item.date}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render() -> None:
    st.caption("Xem lịch học theo ngày hoặc theo tuần, kèm phòng học và giảng viên phụ trách.")
    demo_banner("Thời khóa biểu dưới đây là dữ liệu minh họa, không phải lịch học thật của bạn")

    col1, col2 = st.columns([2, 3])
    with col1:
        mode = st.radio("Chế độ xem", [_MODE_DAY, _MODE_WEEK], horizontal=True, key="schedule_mode")
    with col2:
        anchor = st.date_input("Chọn ngày", value=date.today(), key="schedule_anchor")

    if isinstance(anchor, tuple):  # st.date_input có thể trả tuple khi chọn khoảng
        anchor = anchor[0]

    start, end = _range_for(mode, anchor)
    profile = st.session_state.get("profile")

    with st.spinner("📅 Đang tải lịch học..."):
        result = get_services().schedule.get_schedule(getattr(profile, "student_id", ""), start, end)

    if not result.ok:
        st.error(f"❌ {result.error}")
        return

    items = result.data
    if not items:
        render_empty_state(
            "🌤️",
            "Không có lịch học trong khoảng này",
            f"Từ {start.strftime('%d/%m/%Y')} đến {end.strftime('%d/%m/%Y')} bạn không có buổi học nào.",
        )
        return

    st.caption(f"{len(items)} buổi học · {start.strftime('%d/%m')} – {end.strftime('%d/%m/%Y')}")

    # Nhóm theo ngày để xem tuần dễ đọc hơn là một danh sách phẳng.
    by_date: dict[str, list] = {}
    for item in items:
        by_date.setdefault(item.date, []).append(item)

    for day, day_items in by_date.items():
        if mode == _MODE_WEEK:
            st.markdown(f"#### {day_items[0].weekday} — {day}")
        for item in day_items:
            _render_item(item)
