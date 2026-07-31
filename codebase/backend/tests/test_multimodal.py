"""Tests for dedicated Vision LLM branch and server-controlled media attachments."""
from __future__ import annotations

from backend.rag.multimodal import (
    generate_vision_directions,
    get_map_image_base64,
    get_map_media_asset,
)


def test_get_map_media_asset_returns_valid_metadata():
    asset = get_map_media_asset()
    assert asset["asset_id"] == "vinuni-campus-map-2024"
    assert "Bản đồ" in asset["title"]
    assert "https://vinuni.edu.vn/campus-map/" in asset["url"]


def test_get_map_image_base64_encodes_raw_map_file():
    encoded = get_map_image_base64()
    assert len(encoded) > 0


def test_generate_vision_directions_attaches_media_asset(monkeypatch):
    from backend.rag import multimodal

    monkeypatch.setattr(
        multimodal,
        "generate_vision_text",
        lambda sys, user, img: "Từ Cổng chính, bạn đi thẳng 100m tới Main Building.",
    )

    res = generate_vision_directions(
        "Chỉ đường tới Main Building",
        "Cổng chính VinUniversity (Main Gate)",
        "Main Building",
    )

    assert res["has_evidence"] is True
    assert "1_map.png#khuon-vien" in res["sources"]
    assert len(res["media"]) == 1
    assert res["media"][0]["asset_id"] == "vinuni-campus-map-2024"
    assert "Cổng chính" in res["answer"]

