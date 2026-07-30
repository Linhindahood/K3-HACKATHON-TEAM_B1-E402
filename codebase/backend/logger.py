"""Logger ghi lại câu hỏi & kết quả RAG trên backend.

Mỗi dòng trong file log là JSON object chứa: timestamp, question, answer,
sources, has_evidence, intent, latency_ms.
"""
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent

LOG_DIR = _BACKEND_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "ask_log.jsonl"

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"\b(?:\+84|0)[35789]\d{8}\b")

# Standard Python logger cho console output
logger = logging.getLogger("backend")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    )
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def _redact_pii(text: str) -> str:
    """Mask email addresses and phone numbers in logged strings."""
    if not text:
        return ""
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _PHONE_RE.sub("[REDACTED_PHONE]", text)
    return text


def log_ask(
    *,
    question: str,
    answer: str,
    sources: list[str],
    has_evidence: bool,
    intent: str = "general",
    latency_ms: float = 0.0,
) -> None:
    """Ghi một dòng log Q&A vào file .jsonl và xuất ra console sau khi redaction."""
    safe_question = _redact_pii(question)
    safe_answer = _redact_pii(answer)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": safe_question,
        "answer": safe_answer,
        "sources": sources,
        "has_evidence": has_evidence,
        "intent": intent,
        "latency_ms": round(latency_ms, 1),
    }
    line = json.dumps(entry, ensure_ascii=False) + "\n"

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError as exc:
        logger.warning("Không thể ghi log Q&A: %s", exc)

    logger.info(
        "Q: %s | evidence=%s | latency=%.0fms",
        safe_question[:80],
        has_evidence,
        latency_ms,
    )

