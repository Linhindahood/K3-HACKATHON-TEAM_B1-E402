"""Build and validate the BM25S artifact."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from backend import config
from backend.rag.query_processing import lexical_tokens

SCHEMA_VERSION = "1"
TOKENIZER_VERSION = "unicode-accentless-v1"


def _import_bm25s():
    try:
        import bm25s
    except ImportError as exc:
        raise RuntimeError("Install bm25s before using lexical retrieval") from exc
    return bm25s


def _ordered_chunks(chunks: list[dict]) -> list[dict]:
    if not chunks:
        raise ValueError("chunks must not be empty")
    try:
        return [
            {
                "chunk_id": chunk["chunk_id"],
                "content_hash": chunk["content_hash"],
            }
            for chunk in chunks
        ]
    except KeyError as exc:
        raise ValueError(f"Chunk is missing required metadata: {exc}") from exc


def _chunks_hash(ordered_chunks: list[dict]) -> str:
    payload = json.dumps(
        ordered_chunks,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _index_dir(output_dir: Path | None = None) -> Path:
    return Path(output_dir or Path(config.FAISS_INDEX_DIR) / "bm25")


def build_lexical_artifact(
    chunks: list[dict],
    output_dir: Path | None = None,
) -> Path:
    ordered_chunks = _ordered_chunks(chunks)
    tokenized = [lexical_tokens(chunk["embedding_text"]) for chunk in chunks]
    if any(not tokens for tokens in tokenized):
        raise ValueError("Chunk lexical tokens must not be empty")

    bm25s = _import_bm25s()
    retriever = bm25s.BM25()
    retriever.index(tokenized, show_progress=False)

    destination = _index_dir(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    retriever.save(destination, show_progress=False)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "build_id": _chunks_hash(ordered_chunks)[:16],
        "tokenizer_version": TOKENIZER_VERSION,
        "chunk_count": len(chunks),
        "chunks_hash": _chunks_hash(ordered_chunks),
        "ordered_chunks": ordered_chunks,
    }

    manifest_path = destination / "lexical_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest_path


def load_lexical_artifact(
    chunks: list[dict],
    output_dir: Path | None = None,
):
    ordered_chunks = _ordered_chunks(chunks)
    destination = _index_dir(output_dir)
    try:
        manifest = json.loads(
            (destination / "lexical_manifest.json").read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Lexical artifact is missing; run python -m backend.rag.ingest"
        ) from exc

    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("tokenizer_version") != TOKENIZER_VERSION
    ):
        raise ValueError("Lexical artifact uses a stale tokenizer")
    if (
        manifest.get("chunks_hash") != _chunks_hash(ordered_chunks)
        or manifest.get("ordered_chunks") != ordered_chunks
    ):
        raise ValueError("Lexical artifact is stale for the current chunks")

    bm25s = _import_bm25s()
    retriever = bm25s.BM25.load(destination, load_corpus=False, mmap=False)
    if retriever.scores["num_docs"] != len(chunks):
        raise ValueError("BM25 index size does not match the current chunks")
    return retriever, manifest
