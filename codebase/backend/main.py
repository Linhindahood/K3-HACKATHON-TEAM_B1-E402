"""FastAPI entrypoint — lõi RAG. Discord bot và Streamlit đều gọi vào API này.

Chạy: uvicorn backend.main:app --reload
"""
from fastapi import FastAPI

from backend.api.routes import router

app = FastAPI(title="VinAI Discord Bot — Backend RAG")
app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
