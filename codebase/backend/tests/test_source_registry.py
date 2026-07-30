"""Tests for raw source registry discovery and metadata allowlisting."""
from __future__ import annotations

import pytest
from backend.rag.source_registry import SOURCE_REGISTRY, discover_raw_sources


def test_discover_raw_sources_scans_all_raw_files():
    discovered = discover_raw_sources()
    assert len(discovered) == len(SOURCE_REGISTRY)
    discovered_ids = {src.source_id for src in discovered}
    assert "handbook-ai-in-action" in discovered_ids
    assert "gio-mo-cua-library" in discovered_ids
    assert "vinuni-campus-map" in discovered_ids


def test_registered_sources_have_valid_metadata():
    for source in SOURCE_REGISTRY.values():
        assert source.source_id
        assert source.title
        assert source.local_path
        assert source.source_type in (
            "text",
            "markdown",
            "image",
            "url_list",
            "handbook",
            "library",
        )

        assert source.authority > 0
        assert source.verified_at
