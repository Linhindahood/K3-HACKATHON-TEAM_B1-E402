"""Backward-compatible facade for embedding model and artifact operations."""
from backend.rag.embedding_artifacts import (
    SCHEMA_VERSION,
    build_embedding_artifacts,
    load_embedding_artifacts,
    validate_embedding_artifacts,
)
from backend.rag.embedding_model import (
    DOCUMENT_BATCH_SIZE,
    DOCUMENT_PREFIX,
    QUERY_PREFIX,
    embed_documents,
    embed_query,
    get_model,
    get_runtime_provider,
    normalize_rows,
    select_onnx_provider,
    warm_up,
)

__all__ = [
    "DOCUMENT_BATCH_SIZE",
    "DOCUMENT_PREFIX",
    "QUERY_PREFIX",
    "SCHEMA_VERSION",
    "build_embedding_artifacts",
    "embed_documents",
    "embed_query",
    "get_model",
    "get_runtime_provider",
    "load_embedding_artifacts",
    "normalize_rows",
    "select_onnx_provider",
    "validate_embedding_artifacts",
    "warm_up",
]
