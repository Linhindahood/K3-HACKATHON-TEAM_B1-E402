"""Route /ask — nhận câu hỏi, gọi retriever + generator, đo latency & log."""
import time

# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from pydantic import BaseModel

# pyrefly: ignore [missing-import]
from backend.logger import log_ask
from backend.rag import generator, retriever

router = APIRouter()


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    has_evidence: bool
    intent: str = "general"


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    start_time = time.time()

    passages = retriever.retrieve(payload.question)
    result = generator.generate(payload.question, passages)

    intent = result.get("intent", "general")
    latency_ms = (time.time() - start_time) * 1000.0

    # Ghi log câu hỏi, kết quả & độ trễ xử lý backend
    log_ask(
        question=payload.question,
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        has_evidence=result.get("has_evidence", False),
        intent=intent,
        latency_ms=latency_ms,
    )

    return AskResponse(
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        has_evidence=result.get("has_evidence", False),
        intent=intent,
    )
