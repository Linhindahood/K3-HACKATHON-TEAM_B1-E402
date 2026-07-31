"""Dedicated Vision LLM Branch and Server-Controlled Media Attachments V1."""
from __future__ import annotations

import base64
from pathlib import Path

from backend import config
from backend.rag.llm_provider import LLMProviderError, generate_vision_text
from backend.rag.media_registry import MEDIA_REGISTRY
from backend.rag.prompt import VISION_DIRECTIONS_SYSTEM_PROMPT, build_vision_user_prompt


def get_map_image_base64(raw_dir: Path | None = None) -> str:
    """Encode campus map image 1_map.png as base64 string for Vision LLM API."""
    directory = raw_dir or config.KNOWLEDGE_BASE_RAW_DIR
    image_path = directory / "1_map.png"
    if not image_path.exists():
        return ""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


from backend.rag.source_registry import get_source_metadata


def get_map_media_asset() -> dict:
    """Return official server-controlled media asset metadata for campus map."""
    meta = MEDIA_REGISTRY.get("1_map.png")
    source_meta = get_source_metadata("1_map.png")
    if meta:
        return {
            "asset_id": meta.asset_id,
            "title": source_meta.get("title", "Bản đồ khuôn viên VinUniversity"),
            "url": source_meta.get("public_url", "https://vinuni.edu.vn/campus-map/"),
            "local_path": meta.attachment_key,
            "alt_text": meta.alt_text,
        }
    return {
        "asset_id": "vinuni-campus-map",
        "title": "Bản đồ khuôn viên VinUniversity",
        "url": "https://vinuni.edu.vn/campus-map/",
        "local_path": "1_map.png",
        "alt_text": "Bản đồ các tòa nhà và phòng học VinUniversity",
    }




def generate_vision_directions(question: str, origin: str, destination: str) -> dict:
    """Dedicated Vision LLM Branch for processing location and direction queries with 1_map.png."""
    image_base64 = get_map_image_base64()
    if not image_base64:
        return {
            "answer": "Hiện chưa thể nạp ảnh bản đồ cơ sở vật chất. Bạn vui lòng truy cập https://vinuni.edu.vn/campus-map/ để xem bản đồ trực tuyến nhé.",
            "sources": ["1_map.png#khuon-vien"],
            "has_evidence": False,
            "media": [get_map_media_asset()],
        }

    user_prompt = build_vision_user_prompt(question, origin, destination)

    try:
        raw_answer = generate_vision_text(
            VISION_DIRECTIONS_SYSTEM_PROMPT, user_prompt, image_base64
        )
    except LLMProviderError:
        raw_answer = (
            f"Để di chuyển đến {destination}, bạn có thể xuất phát từ {origin} "
            "và xem sơ đồ lối đi chi tiết trên Bản đồ khuôn viên VinUniversity đính kèm bên dưới."
        )

    # Attach official map link and media asset
    map_asset = get_map_media_asset()
    sources_text = f"\n\nNguồn tham khảo:\n- [{map_asset['title']}]({map_asset['url']})"
    full_answer = f"{raw_answer.rstrip()}{sources_text}"

    return {
        "answer": full_answer,
        "sources": ["1_map.png#khuon-vien"],
        "has_evidence": True,
        "media": [map_asset],
    }
