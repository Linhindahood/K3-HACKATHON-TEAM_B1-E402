"""[Phương] Ghép prompt + gọi LLM, xử lý fallback "hỏi lại" khi thiếu căn cứ.

Provider chọn qua config.LLM_PROVIDER (openai | gemini | openrouter) — cả 3
đều dùng API key thuần, không train model.
"""
from __future__ import annotations

from backend import config

FALLBACK_ANSWER = (
    "Mình chưa tìm thấy thông tin chắc chắn cho câu hỏi này trong tài liệu hiện có. "
    "Bạn có thể hỏi rõ hơn, hoặc liên hệ BTC/TA để được xác nhận nhé."
)


def generate(question: str, passages: list[dict]) -> dict:
    """Stub: chưa gọi LLM thật, luôn trả fallback vì `passages` rỗng.

    TODO(Phương):
    - Nếu `passages` rỗng hoặc score cao nhất < config.SIMILARITY_THRESHOLD
      → trả FALLBACK_ANSWER, has_evidence=False.
    - Ngược lại: ghép prompts/system_prompt.md + few_shot_examples.md + passages,
      gọi LLM theo config.LLM_PROVIDER, trả lời kèm trích nguồn.
    """
    if not passages:
        return {"answer": FALLBACK_ANSWER, "sources": [], "has_evidence": False}

    sources = [p["source"] for p in passages]
    return {"answer": FALLBACK_ANSWER, "sources": sources, "has_evidence": False}
