"""Source Registry for managing raw knowledge base metadata, authority, and public URLs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend import config


@dataclass(frozen=True)
class SourceMetadata:
    source_id: str
    title: str
    local_path: str
    public_url: str | None
    allowed_domains: tuple[str, ...]
    source_type: str
    authority: int
    verified_at: str
    valid_from: str


SOURCE_REGISTRY: dict[str, SourceMetadata] = {
    "1_map.png": SourceMetadata(
        source_id="vinuni-campus-map",
        title="Bản đồ cơ sở vật chất VinUniversity",
        local_path="1_map.png",
        public_url="https://vinuni.edu.vn/vi/visit-2/",
        allowed_domains=("vinuni.edu.vn",),
        source_type="image",
        authority=90,
        verified_at="2026-07-30",
        valid_from="2026-01-01",
    ),
    "2_Handbook_AI_IN_ACTION.txt": SourceMetadata(
        source_id="handbook-ai-in-action",
        title="Handbook AI in Action",
        local_path="2_Handbook_AI_IN_ACTION.txt",
        public_url="https://vinuni.edu.vn/handbook/",
        allowed_domains=("vinuni.edu.vn",),
        source_type="handbook",
        authority=100,
        verified_at="2026-07-30",
        valid_from="2026-01-01",
    ),
    "3_link_vi_tri.txt": SourceMetadata(
        source_id="link-vi-tri-co-so-vat-chat",
        title="Bản đồ & Vị trí cơ sở vật chất VinUniversity",
        local_path="3_link_vi_tri.txt",
        public_url="https://vinuni.edu.vn/vi/visit-2/",
        allowed_domains=("vinuni.edu.vn",),
        source_type="url_list",
        authority=80,
        verified_at="2026-07-30",
        valid_from="2026-01-01",
    ),
    "4_gio_mo_cua_library.txt": SourceMetadata(
        source_id="gio-mo-cua-library",
        title="Giờ mở cửa thư viện VinUniversity",
        local_path="4_gio_mo_cua_library.txt",
        public_url="https://library.vinuni.edu.vn/about-us/hours-and-access/",
        allowed_domains=("library.vinuni.edu.vn", "vinuni.edu.vn"),
        source_type="library",
        authority=95,
        verified_at="2026-07-30",
        valid_from="2026-01-01",
    ),
    "5_ket_qua_khoa_1.txt": SourceMetadata(
        source_id="ket-qua-khoa-1",
        title="Kết quả tổng kết khóa 1",
        local_path="5_ket_qua_khoa_1.txt",
        public_url="https://vinuni.edu.vn/course-results/",
        allowed_domains=("vinuni.edu.vn",),
        source_type="text",
        authority=85,
        verified_at="2026-07-30",
        valid_from="2026-01-01",
    ),
    "6_loai_phong_va_huong_dan_dat_phong.txt": SourceMetadata(
        source_id="loai-phong-va-huong-dan-dat-phong",
        title="Loại phòng và Hướng dẫn đặt phòng thư viện",
        local_path="6_loai_phong_va_huong_dan_dat_phong.txt",
        public_url="https://library.vinuni.edu.vn/room-booking/",
        allowed_domains=("library.vinuni.edu.vn", "vinuni.edu.vn"),
        source_type="library",
        authority=95,
        verified_at="2026-07-30",
        valid_from="2026-01-01",
    ),

    "noi_quy.md": SourceMetadata(
        source_id="noi-quy-khoa-hoc",
        title="Nội quy khóa học VinAI",
        local_path="noi_quy.md",
        public_url="https://vinuni.edu.vn/noi-quy/",
        allowed_domains=("vinuni.edu.vn",),
        source_type="markdown",
        authority=100,
        verified_at="2026-07-30",
        valid_from="2026-01-01",
    ),
    "tien_ich.md": SourceMetadata(
        source_id="tien-ich-sinh-vien",
        title="Tiện ích sinh viên VinUniversity",
        local_path="tien_ich.md",
        public_url="https://vinuni.edu.vn/tien-ich/",
        allowed_domains=("vinuni.edu.vn",),
        source_type="markdown",
        authority=90,
        verified_at="2026-07-30",
        valid_from="2026-01-01",
    ),
    "vi_tri_co_so_vat_chat.md": SourceMetadata(
        source_id="vi-tri-co-so-vat-chat-md",
        title="Vị trí cơ sở vật chất",
        local_path="vi_tri_co_so_vat_chat.md",
        public_url="https://vinuni.edu.vn/facilities/",
        allowed_domains=("vinuni.edu.vn",),
        source_type="markdown",
        authority=90,
        verified_at="2026-07-30",
        valid_from="2026-01-01",
    ),
}


def discover_raw_sources(raw_dir: Path | None = None) -> list[SourceMetadata]:
    """Scan raw directory and discover 100% of raw files against registry."""
    directory = raw_dir or config.KNOWLEDGE_BASE_RAW_DIR
    if not directory.exists():
        raise RuntimeError(f"Knowledge base raw directory does not exist: {directory}")

    discovered = []
    for file_path in sorted(directory.iterdir()):
        if not file_path.is_file():
            continue
        filename = file_path.name
        if filename not in SOURCE_REGISTRY:
            raise RuntimeError(
                f"Unregistered raw document discovered in knowledge_base/raw: {filename}. "
                "Every raw document must be registered in source_registry.py."
            )
        discovered.append(SOURCE_REGISTRY[filename])
    return discovered


def get_source_metadata(filename: str) -> dict:
    """Retrieve metadata dict for registered source filename."""
    meta = SOURCE_REGISTRY.get(filename)
    if meta:
        return {
            "source_id": meta.source_id,
            "title": meta.title,
            "local_path": meta.local_path,
            "public_url": meta.public_url,
            "allowed_domains": meta.allowed_domains,
            "authority": meta.authority,
        }
    return {"title": filename, "public_url": None, "allowed_domains": ()}


