"""HTTP contract for the RAG pipeline."""
from fastapi import APIRouter
from pydantic import BaseModel

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
    result = rag_pipeline.answer_question(payload.question)
    return AskResponse(**result)
