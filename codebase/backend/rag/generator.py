"""Ghép prompt + gọi LLM, xử lý fallback "hỏi lại" khi thiếu căn cứ.

Provider chọn qua config.LLM_PROVIDER (openai | gemini | openrouter) — cả 3
đều dùng API key thuần, không train model.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend import config

FALLBACK_ANSWER = (
    "Mình không tìm thấy thông tin chắc chắn cho câu hỏi này trong tài liệu hiện có. "
    "Bạn có thể hỏi rõ hơn, hoặc liên hệ BTC/TA để được xác nhận nhé."
)


def _load_prompt_template(filename: str) -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / filename
    return prompt_path.read_text(encoding="utf-8")


def _build_context(passages: list[dict[str, Any]]) -> str:
    context_lines: list[str] = []
    for index, passage in enumerate(passages[:3], start=1):
        text = str(passage.get("text", "")).strip()
        source = str(passage.get("source", "")).strip()
        if text:
            context_lines.append(f"{index}. [{source}] {text}")
    return "\n".join(context_lines)


def _build_local_answer(question: str, passages: list[dict[str, Any]]) -> str:
    if not passages:
        return FALLBACK_ANSWER

    top_passage = passages[0]
    text = str(top_passage.get("text", "")).strip()
    source = str(top_passage.get("source", "")).strip()
    question_lower = question.lower()

    if any(keyword in question_lower for keyword in ["đặt lịch", "book phòng", "đặt phòng"]):
        return (
            "Dựa trên tài liệu hiện có, mình chỉ có thể hướng dẫn quy trình đặt lịch/book phòng: "
            "xác định mục đích, liên hệ BTC/TA hoặc bộ phận phụ trách, và chuẩn bị thông tin cần thiết trước khi gửi yêu cầu."
        )

    if text:
        return (
            f"Dựa trên tài liệu hiện có, {text} "
            f"Nếu bạn muốn, mình có thể giải thích thêm hoặc chỉ ra mục liên quan ở nguồn {source}."
        )

    return FALLBACK_ANSWER


def _try_remote_llm(question: str, passages: list[dict[str, Any]]) -> str | None:
    if config.LLM_PROVIDER == "openai" and config.OPENAI_API_KEY:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=config.OPENAI_API_KEY)
            system_prompt = _load_prompt_template("system_prompt.md")
            few_shot_examples = _load_prompt_template("few_shot_examples.md")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{few_shot_examples}\n\nCâu hỏi: {question}\n\nContext:\n{_build_context(passages)}"},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content
            if content:
                return content.strip()
        except Exception:
            return None

    return None


def generate(question: str, passages: list[dict]) -> dict:
    """Dựa trên passages và ngưỡng tương đồng để quyết định có dùng evidence hay không."""
    if not passages:
        return {"answer": FALLBACK_ANSWER, "sources": [], "has_evidence": False}

    scores = []
    for passage in passages:
        score = passage.get("score")
        if score is None:
            scores.append(config.SIMILARITY_THRESHOLD)
        else:
            scores.append(float(score))

    best_score = max(scores, default=0.0)
    if best_score < config.SIMILARITY_THRESHOLD:
        return {"answer": FALLBACK_ANSWER, "sources": [], "has_evidence": False}

    sources = []
    for passage in passages:
        source = str(passage.get("source", "")).strip()
        if source and source not in sources:
            sources.append(source)

    remote_answer = _try_remote_llm(question, passages)
    answer = remote_answer or _build_local_answer(question, passages)
    return {"answer": answer, "sources": sources, "has_evidence": True}
