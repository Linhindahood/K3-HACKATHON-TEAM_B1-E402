"""Tests for media asset registry and landmark metadata."""
from __future__ import annotations

from backend.rag.media_registry import MEDIA_REGISTRY, get_media_asset


def test_media_registry_contains_campus_map():
    map_asset = get_media_asset("1_map.png")
    assert map_asset is not None
    assert map_asset.asset_id == "vinuni-campus-map-2024"
    assert map_asset.media_type == "image/png"
    assert map_asset.landmarks
    assert any("A101" in landmark for landmark in map_asset.landmarks)
