"""Route /ask — nhận câu hỏi, gọi retriever + generator."""
from fastapi import APIRouter
from pydantic import BaseModel

from backend.rag import generator, retriever

router = APIRouter()


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    has_evidence: bool


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    passages = retriever.retrieve(payload.question)
    result = generator.generate(payload.question, passages)
    return AskResponse(**result)
