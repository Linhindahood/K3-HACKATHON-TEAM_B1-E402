"""Local multilingual E5 embeddings and deterministic dense artifacts."""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from backend import config

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

SCHEMA_VERSION = "1"
DOCUMENT_PREFIX = "passage: "
QUERY_PREFIX = "query: "
DOCUMENT_BATCH_SIZE = config.EMBEDDING_BATCH_SIZE


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load one ONNX model instance for the lifetime of the backend process."""
    if config.EMBEDDING_PROVIDER != "local":
        raise ValueError(
            f"Unsupported embedding provider: {config.EMBEDDING_PROVIDER}"
        )
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Install sentence-transformers[onnx] before building embeddings"
        ) from exc

    return _load_cached_or_download(SentenceTransformer)


def _load_cached_or_download(model_class):
    """Avoid network checks after the pinned model has been cached once."""
    model_kwargs = {}
    if config.EMBEDDING_BACKEND == "onnx":
        model_kwargs = {
            "file_name": config.EMBEDDING_ONNX_FILE,
            "provider": config.EMBEDDING_ONNX_PROVIDER,
        }

    cached_path = _cached_model_path()
    if cached_path:
        try:
            return model_class(
                cached_path,
                backend=config.EMBEDDING_BACKEND,
                revision=None,
                model_kwargs=model_kwargs,
                local_files_only=True,
            )
        except OSError:
            pass
    return model_class(
        config.EMBEDDING_MODEL,
        backend=config.EMBEDDING_BACKEND,
        revision=config.EMBEDDING_MODEL_REVISION,
        model_kwargs=model_kwargs,
        local_files_only=False,
    )


def _cached_model_path() -> str | None:
    """Resolve a complete pinned snapshot without making a network request."""
    from huggingface_hub import snapshot_download

    try:
        return snapshot_download(
            repo_id=config.EMBEDDING_MODEL,
            revision=config.EMBEDDING_MODEL_REVISION,
            local_files_only=True,
        )
    except OSError:
        return None


def normalize_rows(vectors: np.ndarray) -> np.ndarray:
    """Return contiguous, L2-normalized float32 row vectors."""
    array = np.asarray(vectors, dtype=np.float32)
    if array.ndim != 2:
        raise ValueError("Embedding output must be a two-dimensional matrix")
    if not np.isfinite(array).all():
        raise ValueError("Embedding output contains NaN or infinity")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("Embedding output contains a zero vector")
    return np.ascontiguousarray(array / norms, dtype=np.float32)


def _encode(texts: list[str], prefix: str, batch_size: int) -> np.ndarray:
    if not texts or any(not text.strip() for text in texts):
        raise ValueError("Embedding inputs must be non-empty strings")
    prefixed = [f"{prefix}{text.strip()}" for text in texts]
    vectors = get_model().encode(
        prefixed,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return normalize_rows(vectors)


def embed_documents(texts: list[str]) -> np.ndarray:
    """Embed document chunks in batches using the E5 passage prefix."""
    if not texts:
        raise ValueError("documents must not be empty")
    return _encode(texts, DOCUMENT_PREFIX, DOCUMENT_BATCH_SIZE)


def embed_query(query: str) -> np.ndarray:
    """Embed one online query with minimal allocation and no model reload."""
    if not query.strip():
        raise ValueError("query must not be empty")
    return _encode([query], QUERY_PREFIX, batch_size=1)[0]


def warm_up() -> None:
    """Load the model and execute one query before serving traffic."""
    embed_query("khởi động hệ thống tìm kiếm")


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


def build_embedding_artifacts(
    chunks: list[dict],
    output_dir: Path | None = None,
) -> tuple[Path, Path, Path]:
    """Embed chunks once and save vectors, exact FAISS index, and manifest."""
    ordered_chunks = _ordered_chunks(chunks)
    vectors = embed_documents([chunk["embedding_text"] for chunk in chunks])
    if vectors.shape[0] != len(chunks):
        raise ValueError("Embedding row count does not match chunk count")

    try:
        import faiss
    except ImportError as exc:
        raise RuntimeError("Install faiss-cpu before building the dense index") from exc

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
        "onnx_provider": config.EMBEDDING_ONNX_PROVIDER,
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


def validate_embedding_artifacts(
    chunks: list[dict],
    output_dir: Path | None = None,
) -> np.ndarray:
    """Validate artifact provenance, shape, normalization, and FAISS order."""
    ordered_chunks = _ordered_chunks(chunks)
    destination = Path(output_dir or config.FAISS_INDEX_DIR)
    embeddings_path = destination / "embeddings.npy"
    index_path = destination / "dense.faiss"
    manifest_path = destination / "embedding_manifest.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current_model = {
        "provider": config.EMBEDDING_PROVIDER,
        "model": config.EMBEDDING_MODEL,
        "model_revision": config.EMBEDDING_MODEL_REVISION,
        "backend": config.EMBEDDING_BACKEND,
        "onnx_file": config.EMBEDDING_ONNX_FILE,
        "onnx_provider": config.EMBEDDING_ONNX_PROVIDER,
    }
    if any(manifest.get(key) != value for key, value in current_model.items()):
        raise ValueError("Embedding artifacts use a stale model configuration")
    expected_hash = _chunks_hash(ordered_chunks)
    if (
        manifest.get("chunks_hash") != expected_hash
        or manifest.get("ordered_chunks") != ordered_chunks
    ):
        raise ValueError("Embedding artifacts are stale for the current chunks")

    vectors = np.load(embeddings_path, allow_pickle=False)
    if vectors.dtype != np.float32 or not np.isfinite(vectors).all():
        raise ValueError("Embedding matrix must contain finite float32 values")
    norms = np.linalg.norm(vectors, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-5):
        raise ValueError("Embedding matrix is not L2-normalized")
    vectors = np.ascontiguousarray(vectors)
    expected_shape = (len(chunks), manifest["dimension"])
    if vectors.shape != expected_shape:
        raise ValueError("Embedding matrix shape does not match its manifest")

    try:
        import faiss
    except ImportError as exc:
        raise RuntimeError("Install faiss-cpu before loading the dense index") from exc
    index = faiss.read_index(str(index_path))
    if index.ntotal != len(chunks) or index.d != vectors.shape[1]:
        raise ValueError("FAISS index shape does not match embedding artifacts")
    return vectors
