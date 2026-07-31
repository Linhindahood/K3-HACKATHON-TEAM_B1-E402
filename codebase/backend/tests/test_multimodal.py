"""Tests for dedicated Vision LLM branch and server-controlled media attachments."""
from __future__ import annotations

from pathlib import Path

from backend.rag.llm_provider import LLMProviderError
from backend.rag.multimodal import (
    generate_vision_directions,
    get_map_media_asset,
)


def test_get_map_media_asset_returns_valid_metadata():
    asset = get_map_media_asset()
    assert asset["asset_id"] == "vinuni-campus-map-2024"
    assert "Bản đồ" in asset["title"]
    assert "https://vinuni.edu.vn/vi/visit-2/" in asset["url"]


def test_generate_directions_attaches_rendered_route_media(monkeypatch, tmp_path):
    from backend.rag import multimodal

    raw_dir = tmp_path / "raw"
    rendered_path = raw_dir / "_generated" / "route-test.png"
    rendered_path.parent.mkdir(parents=True)
    rendered_path.write_bytes(b"png")
    monkeypatch.setattr(multimodal.config, "KNOWLEDGE_BASE_RAW_DIR", raw_dir)
    monkeypatch.setattr(
        multimodal,
        "render_route_map",
        lambda plan: rendered_path,
    )
    monkeypatch.setattr(
        multimodal,
        "generate_text",
        lambda system, user: "Từ Tòa E, bạn đi theo tuyến đã đánh dấu tới Tòa A.",
    )

    res = generate_vision_directions(
        "Đi từ tòa E tới tòa A",
        "tòa E",
        "tòa A",
    )

    assert res["has_evidence"] is True
    assert "1_map.png#route-graph-v1" in res["sources"]
    assert len(res["media"]) == 1
    assert res["media"][0]["local_path"] == "_generated/route-test.png"
    assert Path(rendered_path).exists()
    assert "Tòa E" in res["answer"]


def test_generate_directions_uses_deterministic_text_when_llm_fails(
    monkeypatch,
    tmp_path,
):
    from backend.rag import multimodal

    raw_dir = tmp_path / "raw"
    rendered_path = raw_dir / "_generated" / "route-test.png"
    rendered_path.parent.mkdir(parents=True)
    rendered_path.write_bytes(b"png")
    monkeypatch.setattr(multimodal.config, "KNOWLEDGE_BASE_RAW_DIR", raw_dir)
    monkeypatch.setattr(
        multimodal,
        "render_route_map",
        lambda plan: rendered_path,
    )

    def fail_provider(*args):
        raise LLMProviderError("provider unavailable")

    monkeypatch.setattr(multimodal, "generate_text", fail_provider)

    res = generate_vision_directions(
        "Đi từ tòa E tới tòa A",
        "tòa E",
        "tòa A",
    )

    assert res["has_evidence"] is True
    assert "1." in res["answer"]
    assert "Tòa E" in res["answer"]
    assert "Tòa A" in res["answer"]
    assert res["media"][0]["local_path"] == "_generated/route-test.png"


def test_generate_directions_clarifies_unknown_landmark_without_fake_route(
    monkeypatch,
):
    from backend.rag import multimodal

    monkeypatch.setattr(
        multimodal,
        "render_route_map",
        lambda plan: (_ for _ in ()).throw(AssertionError("Must not render")),
    )
    monkeypatch.setattr(
        multimodal,
        "generate_text",
        lambda *args: (_ for _ in ()).throw(AssertionError("Must not call LLM")),
    )

    res = generate_vision_directions(
        "Đi từ tòa E tới bể bơi",
        "tòa E",
        "bể bơi",
    )

    assert res["has_evidence"] is False
    assert "làm rõ" in res["answer"]
    assert res["media"][0]["local_path"] == "1_map.png"

