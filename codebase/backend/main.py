"""FastAPI entrypoint — lõi RAG. Discord bot và Streamlit đều gọi vào API này.

Chạy: uvicorn backend.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.routes import router
from backend.rag import pipeline

_WARMED_UP = False
_WARMUP_STATS = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _WARMED_UP, _WARMUP_STATS
    try:
        _WARMUP_STATS = pipeline.warm_up()
        _WARMED_UP = True
    except Exception as exc:
        _WARMED_UP = False
        _WARMUP_STATS = {"error": str(exc)}
    yield


app = FastAPI(title="VinAI Discord Bot — Backend RAG", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok" if _WARMED_UP else "degraded",
        "ready": _WARMED_UP,
        "warmup_stats": _WARMUP_STATS,
    }

