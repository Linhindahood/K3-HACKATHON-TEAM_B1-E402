"""Route /ask — nhận câu hỏi, gọi pipeline RAG (retrieve + generate), đo latency & log."""
import time

# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from pydantic import BaseModel

# pyrefly: ignore [missing-import]
from backend.logger import log_ask
from backend.rag import pipeline as rag_pipeline

router = APIRouter()


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    has_evidence: bool


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    start_time = time.time()

    result = rag_pipeline.answer_question(payload.question)

    latency_ms = (time.time() - start_time) * 1000.0

    # Ghi log câu hỏi, kết quả & độ trễ xử lý backend
    log_ask(
        question=payload.question,
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        has_evidence=result.get("has_evidence", False),
        latency_ms=latency_ms,
    )

    return AskResponse(
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        has_evidence=result.get("has_evidence", False),
    )
