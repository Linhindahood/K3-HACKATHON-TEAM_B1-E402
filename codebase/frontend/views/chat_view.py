"""Trang Chat — hỏi đáp RAG với backend thật (POST /ask).

Chuyển từ app.py sang, giữ nguyên hành vi cũ (lịch sử, spinner, badge, citation, media) và
bổ sung: quick action, đánh giá escalation, nút tạo ticket / gặp nhân viên trên từng câu trả lời.
"""
from __future__ import annotations

import streamlit as st

from config import (
    QUICK_ACTIONS,
    SUGGESTED_QUESTIONS,
    TAB_CAPTIONS,
    TAB_CHAT,
)
from services import chat as chat_service
from services import escalation as escalation_service
from ui import (
    clean_answer,
    render_assistant_message,
    render_welcome_screen,
    request_nav,
)


def render_chat_history(messages: list[dict]) -> None:
    """Vẽ lại toàn bộ lịch sử chat (user + assistant, kèm sources/media/intent đã lưu)."""
    for idx, msg in enumerate(messages):
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            render_assistant_message(msg, idx)


def handle_user_turn(question: str) -> None:
    """Xử lý 1 lượt hỏi: lưu + hiển thị câu hỏi, gọi backend, đánh giá escalation, lưu trả lời."""
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.spinner("🔎 Đang tìm kiếm thông tin và tạo câu trả lời..."):
        # Gọi qua module (không `from ... import send_message`) để lời gọi luôn phân giải lại
        # tại runtime — nhờ vậy test monkeypatch được ở đúng 1 chỗ là services.chat.
        result = chat_service.send_message(question)

    # Heuristic phía frontend: backend không trả confidence nên chỉ suy từ intent/evidence/lỗi.
    verdict = escalation_service.assess(
        question,
        intent=result.intent,
        has_evidence=result.has_evidence,
        error=result.error,
        answer=result.answer,
    )
    escalation_payload = {
        "severity": verdict.severity,
        "reason_code": verdict.reason_code,
        "message": verdict.message if verdict.should_offer else "",
        "suggested_category": verdict.suggested_category,
    }

    if result.error:
        assistant_msg = {
            "role": "assistant",
            "content": "",
            "error": result.error,
            "escalation": escalation_payload,
        }
    else:
        assistant_msg = {
            "role": "assistant",
            "content": clean_answer(result.answer),
            "sources": result.sources,
            "has_evidence": result.has_evidence,
            "intent": result.intent,
            "media": result.media,
            "error": None,
            "escalation": escalation_payload,
        }

    st.session_state.messages.append(assistant_msg)
    render_assistant_message(assistant_msg, len(st.session_state.messages) - 1)


def _render_quick_actions() -> str | None:
    """Hàng nút hành động nhanh. Trả về câu hỏi cần gửi nếu người dùng chọn loại `question`."""
    st.markdown("**Hành động nhanh**")
    cols = st.columns(3)
    for idx, action in enumerate(QUICK_ACTIONS):
        with cols[idx % 3]:
            if not st.button(action["label"], key=f"quick_{idx}", use_container_width=True):
                continue
            if action["kind"] == "question":
                return action["value"]
            if action["kind"] == "nav":
                request_nav(action["value"])
            elif action["kind"] == "handover":
                # Người dùng chủ động xin gặp người thật — luôn hợp lệ, không phụ thuộc heuristic.
                st.session_state["handover_ctx"] = {
                    "question": "Sinh viên chủ động yêu cầu gặp nhân viên hỗ trợ.",
                    "answer": "",
                    "intent": "",
                    "has_evidence": None,
                    "sources": [],
                    "escalation": {"severity": "HIGH", "reason_code": "user_request"},
                    "excerpt": st.session_state.get("messages", [])[-6:],
                }
                request_nav("🎫 Yêu cầu của tôi")
    return None


def render() -> None:
    st.caption(TAB_CAPTIONS.get(TAB_CHAT, ""))

    quick_question = _render_quick_actions()
    st.divider()

    messages: list[dict] = st.session_state.messages
    clicked_question: str | None = None
    if not messages:
        active_tab = st.session_state.get("active_tab", TAB_CHAT)
        questions = SUGGESTED_QUESTIONS.get(active_tab, SUGGESTED_QUESTIONS[TAB_CHAT])
        clicked_question = render_welcome_screen(active_tab, questions)
    else:
        render_chat_history(messages)

    typed_question = st.chat_input("Nhập câu hỏi của bạn...")
    # pop() để câu hỏi được bơm từ trang khác chỉ chạy đúng 1 lần, không lặp lại ở rerun sau.
    seeded = st.session_state.pop("pending_question", None)
    prompt = typed_question or quick_question or seeded or clicked_question
    if prompt:
        handle_user_turn(prompt)
