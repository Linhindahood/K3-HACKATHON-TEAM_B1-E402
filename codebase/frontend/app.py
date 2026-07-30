"""Streamlit — UI demo/debug nội bộ cho team (không phải sản phẩm cuối cho sinh viên).

Gọi cùng backend FastAPI mà Discord bot dùng, để test nhanh retrieval + câu trả
lời (kèm nguồn trích dẫn) mà không cần vào Discord.

Chạy: streamlit run frontend/app.py
"""
import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="VinAI Bot — Debug Console", page_icon="🤖")
st.title("VinAI Discord Bot — Debug Console")
st.caption(f"Backend: {BACKEND_URL}")

question = st.text_input("Câu hỏi (nội quy / tiện ích / vị trí cơ sở vật chất)")

if st.button("Hỏi", disabled=not question):
    with st.spinner("Đang hỏi backend..."):
        try:
            response = requests.post(f"{BACKEND_URL}/ask", json={"question": question}, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            st.error(f"Không gọi được backend: {exc}")
        else:
            st.markdown(data["answer"])
            if data["sources"]:
                st.caption("Nguồn: " + ", ".join(data["sources"]))
            st.caption(f"has_evidence = {data['has_evidence']}")
