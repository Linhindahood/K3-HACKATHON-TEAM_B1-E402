"""Resident BM25S index and chunk metadata."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from backend.rag.corpus import load_chunks
from backend.rag.lexical_artifacts import load_lexical_artifact
from backend.rag.query_processing import lexical_tokens


@dataclass(frozen=True)
class LexicalStore:
    retriever: Any
    chunks: tuple[dict, ...]
    manifest: dict | None = None

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def search(self, query: str, top_k: int) -> list[dict]:
        tokens = lexical_tokens(query)
        limit = min(max(top_k, 0), self.chunk_count)
        if not tokens or limit == 0:
            return []

        results = self.retriever.retrieve(
            [tokens],
            k=limit,
            show_progress=False,
        )
        passages = []
        for chunk_index, score in zip(
            results.documents[0],
            results.scores[0],
        ):
            if score <= 0:
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


@lru_cache(maxsize=1)
def get_lexical_store() -> LexicalStore:
    """Keep the validated BM25 index and chunks alive for the process lifetime."""
    chunks = load_chunks()
    retriever, manifest = load_lexical_artifact(chunks)
    return LexicalStore(
        retriever=retriever,
        chunks=tuple(chunks),
        manifest=manifest,
    )
