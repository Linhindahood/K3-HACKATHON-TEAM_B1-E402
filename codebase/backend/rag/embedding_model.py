"""Resident multilingual E5 model lifecycle and inference."""
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np

from backend import config

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

DOCUMENT_PREFIX = "passage: "
QUERY_PREFIX = "query: "
DOCUMENT_BATCH_SIZE = config.EMBEDDING_BATCH_SIZE


def select_onnx_provider(
    configured: str | None = None,
    available: list[str] | None = None,
) -> str:
    """Choose CUDA when available, otherwise use the CPU execution provider."""
    import onnxruntime as ort

    requested = configured or config.EMBEDDING_ONNX_PROVIDER
    providers = available if available is not None else ort.get_available_providers()
    if requested.casefold() == "auto":
        if "CUDAExecutionProvider" in providers:
            return "CUDAExecutionProvider"
        if "CPUExecutionProvider" in providers:
            return "CPUExecutionProvider"
        raise RuntimeError("No supported ONNX execution provider is available")
    if requested not in providers:
        raise RuntimeError(f"ONNX execution provider is unavailable: {requested}")
    return requested


@lru_cache(maxsize=1)
def get_runtime_provider() -> str:
    if config.EMBEDDING_BACKEND != "onnx":
        return config.EMBEDDING_BACKEND
    return select_onnx_provider()


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Keep one model and inference session alive for the process lifetime."""
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
    model_kwargs = {}
    if config.EMBEDDING_BACKEND == "onnx":
        model_kwargs = {
            "file_name": config.EMBEDDING_ONNX_FILE,
            "provider": get_runtime_provider(),
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
    vectors = get_model().encode(
        [f"{prefix}{text.strip()}" for text in texts],
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return normalize_rows(vectors)


def embed_documents(texts: list[str]) -> np.ndarray:
    if not texts:
        raise ValueError("documents must not be empty")
    return _encode(texts, DOCUMENT_PREFIX, DOCUMENT_BATCH_SIZE)


def embed_query(query: str) -> np.ndarray:
    if not query.strip():
        raise ValueError("query must not be empty")
    return _encode([query], QUERY_PREFIX, batch_size=1)[0]


def warm_up() -> None:
    """Load and retain the model, then initialize the selected provider."""
    embed_query("khởi động hệ thống tìm kiếm")
