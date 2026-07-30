"""Build and validate dense vector artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from backend import config
from backend.rag.embedding_model import (
    DOCUMENT_PREFIX,
    QUERY_PREFIX,
    embed_documents,
    get_runtime_provider,
)

SCHEMA_VERSION = "1"


def _ordered_chunks(chunks: list[dict]) -> list[dict]:
    ordered = []
    for chunk in chunks:
        try:
            ordered.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "content_hash": chunk["content_hash"],
                }
            )
        except KeyError as exc:
            raise ValueError(f"Chunk is missing required metadata: {exc}") from exc
        if not chunk.get("embedding_text", "").strip():
            raise ValueError("Chunk embedding_text must not be empty")
    if not ordered:
        raise ValueError("chunks must not be empty")
    return ordered


def _chunks_hash(ordered_chunks: list[dict]) -> str:
    payload = json.dumps(
        ordered_chunks,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _import_faiss():
    try:
        import faiss
    except ImportError as exc:
        raise RuntimeError("Install faiss-cpu before using dense artifacts") from exc
    return faiss


def build_embedding_artifacts(
    chunks: list[dict],
    output_dir: Path | None = None,
) -> tuple[Path, Path, Path]:
    ordered_chunks = _ordered_chunks(chunks)
    vectors = embed_documents([chunk["embedding_text"] for chunk in chunks])
    if vectors.shape[0] != len(chunks):
        raise ValueError("Embedding row count does not match chunk count")

    faiss = _import_faiss()
    destination = Path(output_dir or config.FAISS_INDEX_DIR)
    destination.mkdir(parents=True, exist_ok=True)
    embeddings_path = destination / "embeddings.npy"
    index_path = destination / "dense.faiss"
    manifest_path = destination / "embedding_manifest.json"

    np.save(embeddings_path, vectors, allow_pickle=False)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(index_path))

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "provider": config.EMBEDDING_PROVIDER,
        "model": config.EMBEDDING_MODEL,
        "model_revision": config.EMBEDDING_MODEL_REVISION,
        "backend": config.EMBEDDING_BACKEND,
        "onnx_file": config.EMBEDDING_ONNX_FILE,
        "onnx_provider": get_runtime_provider(),
        "document_prefix": DOCUMENT_PREFIX,
        "query_prefix": QUERY_PREFIX,
        "normalized": True,
        "dtype": "float32",
        "dimension": int(vectors.shape[1]),
        "chunk_count": len(chunks),
        "chunks_hash": _chunks_hash(ordered_chunks),
        "ordered_chunks": ordered_chunks,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return embeddings_path, index_path, manifest_path


def load_embedding_artifacts(
    chunks: list[dict],
    output_dir: Path | None = None,
) -> tuple[np.ndarray, object, dict]:
    """Load and validate vectors and FAISS exactly once for online use."""
    ordered_chunks = _ordered_chunks(chunks)
    destination = Path(output_dir or config.FAISS_INDEX_DIR)
    embeddings_path = destination / "embeddings.npy"
    index_path = destination / "dense.faiss"
    manifest_path = destination / "embedding_manifest.json"

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Dense artifacts are missing; run python -m backend.rag.ingest"
        ) from exc

    current_model = {
        "provider": config.EMBEDDING_PROVIDER,
        "model": config.EMBEDDING_MODEL,
        "model_revision": config.EMBEDDING_MODEL_REVISION,
        "backend": config.EMBEDDING_BACKEND,
        "onnx_file": config.EMBEDDING_ONNX_FILE,
    }
    if any(manifest.get(key) != value for key, value in current_model.items()):
        raise ValueError("Embedding artifacts use a stale model configuration")
    if (
        manifest.get("chunks_hash") != _chunks_hash(ordered_chunks)
        or manifest.get("ordered_chunks") != ordered_chunks
    ):
        raise ValueError("Embedding artifacts are stale for the current chunks")

    try:
        vectors = np.load(embeddings_path, allow_pickle=False)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Embedding matrix is missing; run python -m backend.rag.ingest"
        ) from exc
    if vectors.dtype != np.float32 or not np.isfinite(vectors).all():
        raise ValueError("Embedding matrix must contain finite float32 values")
    norms = np.linalg.norm(vectors, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-5):
        raise ValueError("Embedding matrix is not L2-normalized")
    expected_shape = (len(chunks), manifest["dimension"])
    if vectors.shape != expected_shape:
        raise ValueError("Embedding matrix shape does not match its manifest")

    faiss = _import_faiss()
    try:
        index = faiss.read_index(str(index_path))
    except RuntimeError as exc:
        raise RuntimeError(
            "FAISS index is missing or invalid; run python -m backend.rag.ingest"
        ) from exc
    if index.ntotal != len(chunks) or index.d != vectors.shape[1]:
        raise ValueError("FAISS index shape does not match embedding artifacts")
    return np.ascontiguousarray(vectors), index, manifest


def validate_embedding_artifacts(
    chunks: list[dict],
    output_dir: Path | None = None,
) -> np.ndarray:
    vectors, _, _ = load_embedding_artifacts(chunks, output_dir)
    return vectors
