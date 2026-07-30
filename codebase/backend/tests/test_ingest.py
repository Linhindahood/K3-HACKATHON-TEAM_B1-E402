"""Tests for offline loading, data-aware chunking, and artifact output."""
from __future__ import annotations

import json

from backend.rag import ingest


def _build_chunks() -> tuple[list[dict], list[dict]]:
    documents = ingest.load_raw_documents()
    return documents, ingest.chunk_documents(documents)


def test_loader_uses_only_in_scope_text_sources():
    documents = ingest.load_raw_documents()

    assert {document["source"] for document in documents} == {
        "2_Handbook_AI_IN_ACTION.txt",
        "4_gio_mo_cua_library.txt",
        "6_loai_phong_va_huong_dan_dat_phong.txt",
    }
    assert all(document["text"].strip() for document in documents)
    assert all("TODO" not in document["text"] for document in documents)


def test_chunking_preserves_data_semantics():
    _, chunks = _build_chunks()

    leave_faq = [
        chunk for chunk in chunks if "Quy trình xin nghỉ phép" in chunk["text"]
    ]
    assert len(leave_faq) == 1
    assert "Thông báo trước" in leave_faq[0]["text"]
    assert "Được xác nhận trước khi nghỉ" in leave_faq[0]["text"]

    july_hours = [
        chunk for chunk in chunks if "Giờ mở cửa từ tháng 7 đến tháng 8" in chunk["text"]
    ]
    september_hours = [
        chunk for chunk in chunks if "Giờ mở cửa từ tháng 9" in chunk["text"]
    ]
    assert len(july_hours) == 1
    assert len(september_hours) == 1
    assert july_hours[0]["chunk_id"] != september_hours[0]["chunk_id"]

    outlook = [
        chunk
        for chunk in chunks
        if "HƯỚNG DẪN ĐẶT PHÒNG BẰNG MICROSOFT OUTLOOK" in chunk["text"]
    ]
    assert len(outlook) == 1
    assert all(f"Bước {step}:" in outlook[0]["text"] for step in (1, 2, 3))
    assert outlook[0]["source_url"] == "https://library.vinuni.edu.vn/room-booking/"


def test_room_chunks_are_atomic_and_deduplicated():
    _, chunks = _build_chunks()

    room_a102 = [
        chunk
        for chunk in chunks
        if chunk["heading_path"][-1].casefold() == "phòng a102"
    ]
    assert len(room_a102) == 1
    assert room_a102[0]["source"] == "4_gio_mo_cua_library.txt"
    assert "Sức chứa: 8 chỗ" in room_a102[0]["text"]
    assert "Phòng A103:" not in room_a102[0]["text"]


def test_chunks_are_valid_deterministic_records():
    _, chunks = _build_chunks()

    assert chunks
    assert len({chunk["chunk_id"] for chunk in chunks}) == len(chunks)
    assert len({chunk["content_hash"] for chunk in chunks}) == len(chunks)
    assert all(chunk["source"] for chunk in chunks)
    assert all(chunk["heading_path"] for chunk in chunks)
    assert all(chunk["text"].strip() for chunk in chunks)
    assert all(chunk["embedding_text"].strip() for chunk in chunks)
    assert all("TODO" not in chunk["text"] for chunk in chunks)
    assert all(not ingest.is_url_only(chunk["text"]) for chunk in chunks)
    assert all(len(chunk["text"]) <= ingest.MAX_CHARS for chunk in chunks)


def test_artifact_output_is_reproducible(tmp_path):
    documents, chunks = _build_chunks()

    chunks_path, manifest_path = ingest.write_artifacts(
        documents, chunks, output_dir=tmp_path
    )
    first_chunks = chunks_path.read_bytes()
    first_manifest = manifest_path.read_bytes()

    ingest.write_artifacts(documents, chunks, output_dir=tmp_path)

    assert chunks_path.read_bytes() == first_chunks
    assert manifest_path.read_bytes() == first_manifest

    saved_chunks = [
        json.loads(line)
        for line in chunks_path.read_text(encoding="utf-8").splitlines()
    ]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert saved_chunks == chunks
    assert manifest["schema_version"] == ingest.SCHEMA_VERSION
    assert manifest["chunk_count"] == len(chunks)
    assert manifest["duplicate_count"] >= 1
    assert any(
        item["source"] in ("1_map.jpg", "1_map.png") and item["status"] == "skipped"
        for item in manifest["sources"]
    )

