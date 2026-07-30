"""Load the processed chunks shared by online retrievers."""
from __future__ import annotations

import json

from backend import config


def load_chunks() -> list[dict]:
    chunks_path = config.KNOWLEDGE_BASE_PROCESSED_DIR / "chunks.jsonl"
    try:
        return [
            json.loads(line)
            for line in chunks_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Processed chunks are missing; run python -m backend.rag.ingest"
        ) from exc
