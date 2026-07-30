"""Resident FAISS index and ordered chunk metadata."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np

from backend import config
from backend.rag.embedding_artifacts import load_embedding_artifacts


@dataclass(frozen=True)
class DenseStore:
    index: Any
    chunks: tuple[dict, ...]
    manifest: dict | None = None

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def search(self, query_vector: np.ndarray, top_k: int) -> list[dict]:
        vector = np.asarray(query_vector, dtype=np.float32)
        if vector.ndim != 1 or vector.shape[0] != self.index.d:
            raise ValueError("Query embedding dimension does not match FAISS index")
        limit = min(max(top_k, 0), self.chunk_count)
        if limit == 0:
            return []

        scores, ids = self.index.search(
            np.ascontiguousarray(vector.reshape(1, -1)),
            limit,
        )
        passages = []
        for score, chunk_index in zip(scores[0], ids[0]):
            if chunk_index < 0:
                continue
            chunk = self.chunks[int(chunk_index)]
            passages.append(
                {
                    "text": chunk["text"],
                    "source": f"{chunk['source']}#{chunk['chunk_id']}",
                    "score": float(score),
                    "chunk_id": chunk["chunk_id"],
                    "source_url": chunk.get("source_url"),
                }
            )
        return passages


def _load_chunks() -> list[dict]:
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


@lru_cache(maxsize=1)
def get_dense_store() -> DenseStore:
    """Keep the validated index and chunks alive for the process lifetime."""
    chunks = _load_chunks()
    _, index, manifest = load_embedding_artifacts(chunks)
    return DenseStore(index=index, chunks=tuple(chunks), manifest=manifest)
