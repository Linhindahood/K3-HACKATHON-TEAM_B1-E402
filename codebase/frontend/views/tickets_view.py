"""Trang "Yêu cầu của tôi" — tạo ticket, theo dõi trạng thái, và handover sang người thật.

Đây là nơi thể hiện nửa sau của vòng đời sản phẩm:
TẠO YÊU CẦU → ĐỊNH TUYẾN → THEO DÕI → HANDOVER NGƯỜI THẬT.

Toàn bộ dữ liệu là DEMO (lưu .local_store/*.jsonl) vì backend chưa có API ticket.
"""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from config import TICKET_CATEGORIES, DEPARTMENT_BY_CATEGORY, DEFAULT_DEPARTMENT
from services import escalation as escalation_service
from services.factory import get_services
from services.models import (
    PRIORITIES,
    PRIORITY_NORMAL,
    HandoverDraft,
    TicketDraft,
)
from ui import (
    demo_banner,
    format_source_label,
    priority_pill_html,
    render_empty_state,
    severity_notice_html,
    status_pill_html,
)

_CATEGORY_LABELS = dict(TICKET_CATEGORIES)
_CATEGORY_KEYS = [key for key, _ in TICKET_CATEGORIES]


def _format_dt(value: str) -> str:
    """ISO -> 'dd/mm/yyyy HH:MM' theo giờ máy, dễ đọc hơn cho sinh viên."""
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value or "—"
    if dt.tzinfo is not None:
        dt = dt.astimezone()
    return dt.strftime("%d/%m/%Y %H:%M")


def _elapsed_label(value: str) -> str:
    """Thời gian chờ tính từ lúc gửi — dùng cho trạng thái handover."""
    try:
        started = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return "—"
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    minutes = int((datetime.now(timezone.utc) - started).total_seconds() // 60)
    if minutes < 1:
        return "vừa xong"
    if minutes < 60:
        return f"{minutes} phút trước"
    return f"{minutes // 60} giờ {minutes % 60} phút trước"


def _render_create_form(draft_ctx: dict | None) -> None:
    """Form tạo ticket. `draft_ctx` là ngữ cảnh prefill từ 1 câu trả lời trong chat (nếu có)."""
    ctx = draft_ctx or {}
    escalation_info = ctx.get("escalation") or {}
    reason_code = escalation_info.get("reason_code", "")

    if ctx:
        st.info("📎 Yêu cầu này được tạo từ một câu trả lời trong Chat — ngữ cảnh đã được đính kèm sẵn.")

    suggested_category = escalation_info.get("suggested_category") or "khac"
    default_cat_idx = _CATEGORY_KEYS.index(suggested_category) if suggested_category in _CATEGORY_KEYS else len(_CATEGORY_KEYS) - 1

    suggested_priority = get_services().tickets.suggest_priority(
        urgent=reason_code == escalation_service.REASON_URGENT_KEYWORD,
        sensitive=reason_code == escalation_service.REASON_SENSITIVE_KEYWORD,
        unsupported=reason_code == escalation_service.REASON_UNSUPPORTED_ACTION,
    ) if get_services().using_mock else PRIORITY_NORMAL

    with st.form("ticket_form", clear_on_submit=False):
        subject = st.text_input(
            "Tiêu đề *",
            value=(ctx.get("question") or "")[:120],
            placeholder="VD: Không đăng ký được môn Machine Learning",
        )
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                "Danh mục *",
                _CATEGORY_KEYS,
                index=default_cat_idx,
                format_func=lambda key: _CATEGORY_LABELS.get(key, key),
            )
        with col2:
            priority = st.selectbox(
                "Mức ưu tiên",
                PRIORITIES,
                index=PRIORITIES.index(suggested_priority) if suggested_priority in PRIORITIES else 1,
            )

        # Cố ý để trống: đây là phần sinh viên tự mô tả vấn đề. Câu trả lời của AI đã được
        # đính kèm riêng qua source_answer nên không cần nhét vào ô này.
        description = st.text_area(
            "Mô tả chi tiết *",
            placeholder="Mô tả vấn đề bạn gặp phải, kèm mã học phần / học kỳ / thông báo lỗi nếu có.",
            height=140,
        )

        # Department là business rule, hiển thị để minh bạch nhưng KHÔNG cho user tự chọn.
        st.caption(f"➡️ Sẽ được định tuyến tới: **{DEPARTMENT_BY_CATEGORY.get(category, DEFAULT_DEPARTMENT)}**")

        submitted = st.form_submit_button("🎫 Gửi yêu cầu", use_container_width=True)

    if not submitted:
        return

    profile = st.session_state.get("profile")
    draft = TicketDraft(
        subject=subject,
        category=category,
        description=description,
        priority=priority,
        student_id=getattr(profile, "student_id", ""),
        source_question=ctx.get("question", ""),
        source_answer=ctx.get("answer", ""),
        source_intent=ctx.get("intent", ""),
        has_evidence=ctx.get("has_evidence"),
        source_refs=ctx.get("sources", []),
        conversation_excerpt=ctx.get("excerpt", []),
    )
    result = get_services().tickets.create_ticket(draft)

    if not result.ok:
        # Không được nói "đã tạo" khi thất bại.
        st.error(f"❌ Chưa tạo được yêu cầu. {result.error}")
        return

    st.session_state.pop("ticket_draft", None)
    st.session_state["selected_ticket_id"] = result.data.ticket_id
    st.success(f"✅ Đã tạo yêu cầu **{result.data.ticket_id}** — định tuyến tới {result.data.department}.")
    st.rerun()


def _render_handover_panel(ctx: dict) -> None:
    """Xác nhận chuyển sang nhân viên thật, kèm bản tóm tắt sẽ gửi cho nhân viên."""
    escalation_info = ctx.get("escalation") or {}
    severity = escalation_info.get("severity", "HIGH")
    message = escalation_info.get("message") or "Bạn đang yêu cầu được hỗ trợ bởi nhân viên."

    st.markdown("### 👨‍💼 Chuyển cho nhân viên hỗ trợ")
    st.markdown(severity_notice_html(severity, message), unsafe_allow_html=True)

    with st.expander("📄 Tóm tắt sẽ gửi cho nhân viên", expanded=True):
        st.markdown(f"**Câu hỏi:** {ctx.get('question') or '—'}")
        if ctx.get("answer"):
            st.markdown(f"**AI đã trả lời:** {ctx['answer'][:400]}")
        st.markdown(f"**Lý do chuyển:** `{escalation_info.get('reason_code') or 'user_request'}`")
        if ctx.get("sources"):
            st.markdown("**Nguồn AI đã dùng:** " + ", ".join(format_source_label(s) for s in ctx["sources"]))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Xác nhận chuyển", key="ho_confirm", use_container_width=True):
            profile = st.session_state.get("profile")
            result = get_services().handover.request_handover(
                HandoverDraft(
                    question=ctx.get("question", ""),
                    answer_excerpt=ctx.get("answer", "")[:400],
                    reason_code=escalation_info.get("reason_code", "user_request"),
                    severity=severity,
                    student_id=getattr(profile, "student_id", ""),
                )
            )
            if not result.ok:
                st.error(f"❌ {result.error}")
                return
            st.session_state.pop("handover_ctx", None)
            st.success(f"✅ Đã chuyển. Mã handover: **{result.data.handover_id}**")
            st.rerun()
    with col2:
        if st.button("Hủy", key="ho_cancel", use_container_width=True):
            st.session_state.pop("handover_ctx", None)
            st.rerun()


def _render_ticket_detail(ticket) -> None:
    st.markdown(f"### {ticket.ticket_id} — {ticket.subject}")
    st.markdown(
        status_pill_html(ticket.status) + priority_pill_html(ticket.priority)
        + f'<span class="c24-badge c24-badge-gray">🏢 {ticket.department}</span>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="c24-meta">Tạo lúc {_format_dt(ticket.created_at)} · Cập nhật {_format_dt(ticket.updated_at)}</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("**Mô tả**")
    st.markdown(ticket.description or "_(trống)_")

    if ticket.source_question:
        with st.expander("💬 Ngữ cảnh từ hội thoại"):
            st.markdown(f"**Câu hỏi:** {ticket.source_question}")
            if ticket.source_answer:
                st.markdown(f"**AI trả lời:** {ticket.source_answer[:800]}")
            if ticket.source_refs:
                st.markdown("**Nguồn:** " + ", ".join(format_source_label(s) for s in ticket.source_refs))

    if ticket.events:
        with st.expander(f"🕓 Lịch sử xử lý ({len(ticket.events)})", expanded=True):
            for event in ticket.events:
                st.markdown(f"- `{_format_dt(event.at)}` — **{event.actor}**: {event.note}")

    services = get_services()
    next_status = services.tickets.next_status_for(ticket.status) if services.using_mock else ""
    col1, col2 = st.columns(2)
    with col1:
        if next_status and st.button(f"⏩ Mô phỏng xử lý → {next_status} (DEMO)", key=f"tk_adv_{ticket.ticket_id}", use_container_width=True):
            result = services.tickets.update_ticket_status(ticket.ticket_id, next_status)
            if not result.ok:
                st.error(result.error)
            else:
                st.rerun()
    with col2:
        if st.button("⬅️ Quay lại danh sách", key=f"tk_back_{ticket.ticket_id}", use_container_width=True):
            st.session_state.pop("selected_ticket_id", None)
            st.rerun()


def _render_ticket_list() -> None:
    profile = st.session_state.get("profile")
    result = get_services().tickets.list_tickets(student_id=getattr(profile, "student_id", ""))

    if not result.ok:
        st.error(f"❌ {result.error}")
        return

    tickets = result.data
    if not tickets:
        render_empty_state(
            "📭",
            "Bạn chưa có yêu cầu nào",
            "Tạo yêu cầu mới ở tab bên trên, hoặc bấm '🎫 Tạo yêu cầu hỗ trợ' ngay dưới một câu trả lời trong Chat.",
        )
        return

    status_options = ["Tất cả"] + sorted({t.status for t in tickets})
    chosen = st.selectbox("Lọc theo trạng thái", status_options, key="tk_filter")
    if chosen != "Tất cả":
        tickets = [t for t in tickets if t.status == chosen]

    st.caption(f"{len(tickets)} yêu cầu")
    for ticket in tickets:
        st.markdown(
            f'<div class="c24-card">'
            f'<div class="c24-card-title">{ticket.ticket_id} — {ticket.subject}</div>'
            f"{status_pill_html(ticket.status)}{priority_pill_html(ticket.priority)}"
            f'<span class="c24-badge c24-badge-gray">🏢 {ticket.department}</span>'
            f'<div class="c24-meta">Tạo lúc {_format_dt(ticket.created_at)}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("Xem chi tiết", key=f"tk_detail_{ticket.ticket_id}", use_container_width=True):
            st.session_state["selected_ticket_id"] = ticket.ticket_id
            st.rerun()


def _render_handover_status() -> None:
    result = get_services().handover.list_handovers()
    if not result.ok or not result.data:
        return
    st.divider()
    st.markdown("### 👨‍💼 Yêu cầu gặp nhân viên")
    for item in result.data:
        st.markdown(
            f'<div class="c24-card">'
            f'<div class="c24-card-title">{item.handover_id}</div>'
            f'<span class="c24-badge c24-badge-amber">⏳ {item.status}</span>'
            f'<span class="c24-badge c24-badge-gray">👥 {item.assigned_to}</span>'
            f'<div class="c24-meta">Gửi {_elapsed_label(item.requested_at)} · '
            f"Dự kiến phản hồi trong ~{item.eta_minutes} phút (ước tính demo)</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


def render() -> None:
    st.caption("Tạo yêu cầu hỗ trợ, theo dõi tiến độ xử lý và chuyển cho nhân viên khi cần.")
    demo_banner("Ticket và handover được lưu cục bộ trên máy bạn")

    # Handover được ưu tiên hiển thị: nó là hành động người dùng vừa chủ động yêu cầu.
    handover_ctx = st.session_state.get("handover_ctx")
    if handover_ctx:
        _render_handover_panel(handover_ctx)
        st.divider()

    selected_id = st.session_state.get("selected_ticket_id")
    if selected_id:
        result = get_services().tickets.get_ticket(selected_id)
        if result.ok:
            _render_ticket_detail(result.data)
            return
        st.warning(result.error)
        st.session_state.pop("selected_ticket_id", None)

    tab_list, tab_create = st.tabs(["📋 Danh sách yêu cầu", "➕ Tạo yêu cầu mới"])
    with tab_list:
        _render_ticket_list()
        _render_handover_status()
    with tab_create:
        _render_create_form(st.session_state.get("ticket_draft"))
