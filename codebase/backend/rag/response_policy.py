"""Response policy and refusal taxonomy for RAG V1."""
from __future__ import annotations

import re

from backend.rag.router import Intent

GREETING_RESPONSE = (
    "Chào bạn! Mình là Bot hỗ trợ học viên VinAI. "
    "Bạn cần mình giúp thông tin gì về nội quy, tiện ích hay cơ sở vật chất hôm nay?"
)

IDENTITY_RESPONSE = (
    "Mình là Chatbot hỗ trợ học viên khóa thực chiến VinAI, "
    "chuyên giải đáp các thắc mắc về Nội quy khóa học/trường, Tiện ích sinh viên "
    "và Vị trí cơ sở vật chất dựa trên tài liệu chính thức."
)

HELP_RESPONSE = (
    "Mình có thể hỗ trợ bạn tra cứu 3 nhóm thông tin chính:\n"
    "1. Nội quy khóa học và văn hóa học tập VinAI.\n"
    "2. Tiện ích sinh viên (giờ mở cửa thư viện, wifi, dịch vụ...).\n"
    "3. Vị trí cơ sở vật chất và sơ đồ khuôn viên VinUniversity."
)

UNSUPPORTED_ACTION_RESPONSE = (
    "Mình là AI hỗ trợ thông tin nên không thể trực tiếp thực hiện các thao tác hay hành động thay bạn. "
    "Tuy nhiên, mình có thể hướng dẫn bạn quy trình và các bước thực hiện dựa trên tài liệu chính thức. "
    "Bạn cần mình hướng dẫn quy trình nào?"
)

NO_EVIDENCE_ANSWER = (
    "Mình chưa tìm thấy thông tin chắc chắn cho câu hỏi này trong tài liệu hiện có. "
    "Bạn có thể hỏi rõ hơn, hoặc liên hệ BTC/TA để được xác nhận nhé."
)

OUT_OF_SCOPE_ANSWER = (
    "Câu hỏi này nằm ngoài dữ liệu tài liệu hiện tại của mình. "
    "Mình chỉ hỗ trợ 3 nhóm thông tin: Nội quy khóa học, Tiện ích sinh viên và Vị trí cơ sở vật chất. "
    "Bạn có thể liên hệ BTC/TA để được tư vấn thêm nhé."
)

PROVIDER_FAILURE_ANSWER = (
    "Mình đã tìm thấy tài liệu liên quan nhưng hiện chưa thể tạo câu trả lời. "
    "Bạn vui lòng thử lại sau nhé."
)


def get_deterministic_response(intent: Intent) -> dict:
    """Return fast deterministic response dictionary for non-factual intents."""
    if intent == Intent.GREETING:
        return {"answer": GREETING_RESPONSE, "sources": [], "has_evidence": False}
    elif intent == Intent.IDENTITY:
        return {"answer": IDENTITY_RESPONSE, "sources": [], "has_evidence": False}
    elif intent == Intent.HELP:
        return {"answer": HELP_RESPONSE, "sources": [], "has_evidence": False}
    elif intent == Intent.UNSUPPORTED_ACTION:
        return {
            "answer": UNSUPPORTED_ACTION_RESPONSE,
            "sources": [],
            "has_evidence": False,
        }
    elif intent == Intent.OUT_OF_SCOPE:
        return {
            "answer": OUT_OF_SCOPE_ANSWER,
            "sources": [],
            "has_evidence": False,
        }
    raise ValueError(f"No deterministic response for intent {intent}")



def strip_internal_leakage(text: str) -> str:
    """Ensure raw LLM output contains zero local filenames, chunk IDs, or [Sx] markers."""
    # Remove bracketed citation markers like [S1], [S2]
    cleaned = re.sub(r"\[S\d+\]", "", text)
    # Remove raw txt/md filenames if accidentally output by model
    cleaned = re.sub(r"\b\d+_[A-Za-z0-9_]+\.(?:txt|md)\b", "", cleaned)
    # Clean up redundant empty lines
    lines = [line.rstrip() for line in cleaned.splitlines()]
    return "\n".join(lines).strip()
