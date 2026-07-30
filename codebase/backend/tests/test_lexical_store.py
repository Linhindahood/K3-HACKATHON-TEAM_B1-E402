"""Tests for BM25S artifacts and resident lexical retrieval."""
from __future__ import annotations

import json

import pytest

from backend.rag import lexical_artifacts, lexical_store


def _chunks() -> list[dict]:
    return [
        {
            "chunk_id": "hours",
            "content_hash": "hash-hours",
            "source": "library.txt",
            "text": "Giờ mở cửa thư viện",
            "embedding_text": "Thư viện > Giờ mở cửa\nMở cửa lúc 8 giờ.",
            "source_url": "https://example.com/hours",
        },
        {
            "chunk_id": "room-a102",
            "content_hash": "hash-a102",
            "source": "library.txt",
            "text": "Phòng A102 có 8 chỗ",
            "embedding_text": "Thư viện > Phòng A102\nSức chứa: 8 chỗ.",
            "source_url": "https://example.com/rooms",
        },
    ]


def test_bm25_artifact_reloads_and_matches_unaccented_query(tmp_path):
    manifest_path = lexical_artifacts.build_lexical_artifact(
        _chunks(),
        output_dir=tmp_path,
    )
    retriever, manifest = lexical_artifacts.load_lexical_artifact(
        _chunks(),
        output_dir=tmp_path,
    )
    store = lexical_store.LexicalStore(
        retriever=retriever,
        chunks=tuple(_chunks()),
        manifest=manifest,
    )

    passages = store.search("phong A102 co bao nhieu cho", top_k=2)

    assert manifest_path.name == "lexical_manifest.json"
    assert passages[0]["chunk_id"] == "room-a102"
    assert passages[0]["score"] > 0


def test_bm25_artifact_rejects_stale_chunks(tmp_path):
    chunks = _chunks()
    lexical_artifacts.build_lexical_artifact(chunks, output_dir=tmp_path)
    chunks[0]["content_hash"] = "changed"

    with pytest.raises(ValueError, match="stale"):
        lexical_artifacts.load_lexical_artifact(chunks, output_dir=tmp_path)


def test_bm25_artifact_rejects_stale_tokenizer(tmp_path):
    lexical_artifacts.build_lexical_artifact(_chunks(), output_dir=tmp_path)
    manifest_path = tmp_path / "lexical_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["tokenizer_version"] = "old"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="tokenizer"):
        lexical_artifacts.load_lexical_artifact(
            _chunks(),
            output_dir=tmp_path,
        )


def test_lexical_store_loader_is_resident(monkeypatch):
    lexical_store.get_lexical_store.cache_clear()
    calls: list[str] = []
    chunks = _chunks()
    monkeypatch.setattr(lexical_store, "load_chunks", lambda: chunks)
    monkeypatch.setattr(
        lexical_store,
        "load_lexical_artifact",
        lambda loaded_chunks: (
            calls.append("load") or ("retriever", {"chunk_count": 2})
        ),
    )

    first = lexical_store.get_lexical_store()
    second = lexical_store.get_lexical_store()

    assert first is second
    assert calls == ["load"]
    lexical_store.get_lexical_store.cache_clear()
