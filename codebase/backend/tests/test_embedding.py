"""Tests for local E5 embedding and dense-index artifacts."""
from __future__ import annotations

import json

import numpy as np
import pytest

from backend.rag import embedding


class FakeModel:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], dict]] = []

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        self.calls.append((texts, kwargs))
        return np.asarray(
            [[index + 1.0, len(text)] for index, text in enumerate(texts)],
            dtype=np.float32,
        )


class FakeModelLoader:
    calls: list[tuple[str, bool]] = []

    def __new__(cls, *args, **kwargs):
        cls.calls.append((args[0], kwargs["local_files_only"]))
        return "loaded-model"


def _chunks() -> list[dict]:
    return [
        {
            "chunk_id": "library-hours",
            "content_hash": "hash-hours",
            "embedding_text": "Thư viện > Giờ mở cửa\nMở cửa lúc 8 giờ.",
        },
        {
            "chunk_id": "room-a102",
            "content_hash": "hash-a102",
            "embedding_text": "Thư viện > Phòng A102\nSức chứa: 8 chỗ.",
        },
    ]


def test_e5_uses_asymmetric_prefixes_and_normalized_float32(monkeypatch):
    model = FakeModel()
    monkeypatch.setattr(embedding, "get_model", lambda: model)

    documents = embedding.embed_documents(["tài liệu một", "tài liệu hai"])
    query = embedding.embed_query("phòng A102 có bao nhiêu chỗ?")

    assert model.calls[0][0] == [
        "passage: tài liệu một",
        "passage: tài liệu hai",
    ]
    assert model.calls[1][0] == ["query: phòng A102 có bao nhiêu chỗ?"]
    assert model.calls[0][1]["batch_size"] == embedding.DOCUMENT_BATCH_SIZE
    assert documents.dtype == np.float32
    assert query.dtype == np.float32
    assert query.shape == (2,)
    np.testing.assert_allclose(np.linalg.norm(documents, axis=1), 1.0)
    np.testing.assert_allclose(np.linalg.norm(query), 1.0)


def test_empty_inputs_are_rejected():
    with pytest.raises(ValueError, match="documents"):
        embedding.embed_documents([])
    with pytest.raises(ValueError, match="query"):
        embedding.embed_query("   ")


def test_model_loader_uses_cached_snapshot_without_network(monkeypatch):
    FakeModelLoader.calls = []
    monkeypatch.setattr(embedding, "_cached_model_path", lambda: "cached/snapshot")

    model = embedding._load_cached_or_download(FakeModelLoader)

    assert model == "loaded-model"
    assert FakeModelLoader.calls == [("cached/snapshot", True)]


def test_model_loader_downloads_only_when_snapshot_is_missing(monkeypatch):
    FakeModelLoader.calls = []
    monkeypatch.setattr(embedding, "_cached_model_path", lambda: None)

    model = embedding._load_cached_or_download(FakeModelLoader)

    assert model == "loaded-model"
    assert FakeModelLoader.calls == [
        ("intfloat/multilingual-e5-small", False)
    ]


def test_model_loader_redownloads_incomplete_cached_snapshot(monkeypatch):
    class IncompleteCacheLoader(FakeModelLoader):
        def __new__(cls, *args, **kwargs):
            cls.calls.append((args[0], kwargs["local_files_only"]))
            if kwargs["local_files_only"]:
                raise OSError("incomplete snapshot")
            return "loaded-model"

    IncompleteCacheLoader.calls = []
    monkeypatch.setattr(embedding, "_cached_model_path", lambda: "cached/snapshot")

    model = embedding._load_cached_or_download(IncompleteCacheLoader)

    assert model == "loaded-model"
    assert IncompleteCacheLoader.calls == [
        ("cached/snapshot", True),
        ("intfloat/multilingual-e5-small", False),
    ]


def test_embedding_artifacts_preserve_chunk_order_and_reload(tmp_path, monkeypatch):
    vectors = np.asarray([[3.0, 4.0], [0.0, 2.0]], dtype=np.float32)
    monkeypatch.setattr(
        embedding,
        "embed_documents",
        lambda texts: embedding.normalize_rows(vectors),
    )

    embeddings_path, index_path, manifest_path = (
        embedding.build_embedding_artifacts(_chunks(), output_dir=tmp_path)
    )
    loaded = embedding.validate_embedding_artifacts(_chunks(), output_dir=tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert embeddings_path.name == "embeddings.npy"
    assert index_path.name == "dense.faiss"
    assert manifest_path.name == "embedding_manifest.json"
    assert loaded.shape == (2, 2)
    assert loaded.dtype == np.float32
    assert manifest["chunk_count"] == 2
    assert manifest["dimension"] == 2
    assert manifest["ordered_chunks"] == [
        {"chunk_id": "library-hours", "content_hash": "hash-hours"},
        {"chunk_id": "room-a102", "content_hash": "hash-a102"},
    ]


def test_validation_rejects_stale_chunk_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(
        embedding,
        "embed_documents",
        lambda texts: np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
    )
    chunks = _chunks()
    embedding.build_embedding_artifacts(chunks, output_dir=tmp_path)
    chunks[0]["content_hash"] = "changed"

    with pytest.raises(ValueError, match="stale"):
        embedding.validate_embedding_artifacts(chunks, output_dir=tmp_path)


def test_validation_rejects_stale_model_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(
        embedding,
        "embed_documents",
        lambda texts: np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
    )
    embedding.build_embedding_artifacts(_chunks(), output_dir=tmp_path)
    manifest_path = tmp_path / "embedding_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["model"] = "different-model"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="model configuration"):
        embedding.validate_embedding_artifacts(_chunks(), output_dir=tmp_path)
