"""Media Registry for managing image assets, alt text, and landmark sidecar metadata."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaAsset:
    asset_id: str
    source_id: str
    attachment_key: str
    media_type: str
    alt_text: str
    landmarks: tuple[str, ...]


MEDIA_REGISTRY: dict[str, MediaAsset] = {
    "1_map.png": MediaAsset(
        asset_id="vinuni-campus-map-2024",
        source_id="vinuni-campus-map",
        attachment_key="1_map.png",
        media_type="image/png",
        alt_text="Bản đồ các tòa nhà và phòng học VinUniversity",
        landmarks=(
            "Tòa nhà A - Thư viện & Phòng học",
            "Phòng A101, A102, A103",
            "Tòa nhà B - Khu hành chính",
            "Khu tự học sinh viên",
        ),
    )
}


def get_media_asset(filename: str) -> MediaAsset | None:
    return MEDIA_REGISTRY.get(filename)
