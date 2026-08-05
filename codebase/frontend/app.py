"""Streamlit — Campus 24/7, giao diện demo/debug nội bộ cho team.

Gọi cùng backend FastAPI (POST /ask, GET /health) mà Discord bot dùng — không tự chứa logic RAG.

Chạy: streamlit run frontend/app.py
"""
from __future__ import annotations

import streamlit as st

from api_client import ask_rag, check_health
from config import (
    ABOUT_TEXT,
    APP_SUBTITLE,
    APP_TITLE,
    SUGGESTED_QUESTIONS,
    TAB_ABOUT,
    TAB_CAPTIONS,
    TAB_CHAT,
)
from ui import CUSTOM_CSS, clean_answer, render_assistant_message, render_sidebar, render_welcome_screen


def init_session_state() -> None:
    """Khởi tạo lịch sử hội thoại nếu chưa có — giữ nguyên khi Streamlit rerun trong cùng session."""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_chat_history(messages: list[dict]) -> None:
    """Vẽ lại toàn bộ lịch sử chat (user + assistant, kèm sources/media/intent đã lưu)."""
    for msg in messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            render_assistant_message(msg)


def handle_user_turn(question: str) -> None:
    """Xử lý 1 lượt hỏi: lưu + hiển thị câu hỏi, gọi backend, lưu + hiển thị câu trả lời."""
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.spinner("🔎 Đang tìm kiếm thông tin và tạo câu trả lời..."):
        result = ask_rag(question)

    if result.error:
        assistant_msg = {"role": "assistant", "content": "", "error": result.error}
    else:
        assistant_msg = {
            "role": "assistant",
            "content": clean_answer(result.answer),
            "sources": result.sources,
            "has_evidence": result.has_evidence,
            "intent": result.intent,
            "media": result.media,
            "error": None,
        }
    st.session_state.messages.append(assistant_msg)
    render_assistant_message(assistant_msg)


def main() -> None:
    st.set_page_config(page_title="Campus 24/7", page_icon="🎓", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_session_state()

    active_tab = render_sidebar()

    st.markdown(f"# {APP_TITLE}")
    st.caption(APP_SUBTITLE)
    health = check_health()
    st.caption("🟢 Online" if health.get("ready") else "🔴 Offline")

    if active_tab == TAB_ABOUT:
        st.markdown(ABOUT_TEXT)
        return

    caption = TAB_CAPTIONS.get(active_tab)
    if caption:
        st.caption(caption)

    messages: list[dict] = st.session_state.messages
    clicked_question: str | None = None
    if not messages:
        questions = SUGGESTED_QUESTIONS.get(active_tab, SUGGESTED_QUESTIONS[TAB_CHAT])
        clicked_question = render_welcome_screen(questions)
    else:
        render_chat_history(messages)

    typed_question = st.chat_input("Nhập câu hỏi của bạn...")
    prompt = typed_question or clicked_question
    if prompt:
        handle_user_turn(prompt)


if __name__ == "__main__":
    main()
