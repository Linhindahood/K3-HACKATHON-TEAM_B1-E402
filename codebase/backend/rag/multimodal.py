"""Grounded direction text and deterministic rendered route attachments."""
from __future__ import annotations

from pathlib import Path

from backend import config
from backend.rag.llm_provider import LLMProviderError, generate_text
from backend.rag.map_renderer import render_route_map
from backend.rag.media_registry import MEDIA_REGISTRY
from backend.rag.prompt import (
    ROUTE_DIRECTIONS_SYSTEM_PROMPT,
    build_route_directions_prompt,
)
from backend.rag.route_graph import (
    RouteNotFoundError,
    RoutePlan,
    UnknownLandmarkError,
    plan_route,
)
from backend.rag.source_registry import get_source_metadata


def get_map_media_asset() -> dict:
    """Return official server-controlled media asset metadata for campus map."""
    meta = MEDIA_REGISTRY.get("1_map.png")
    source_meta = get_source_metadata("3_link_vi_tri.txt")
    url = source_meta.get("public_url") or "https://vinuni.edu.vn/vi/visit-2/"
    if meta:
        return {
            "asset_id": meta.asset_id,
            "title": source_meta.get("title", "Bản đồ khuôn viên VinUniversity"),
            "url": url,
            "local_path": meta.attachment_key,
            "alt_text": meta.alt_text,
        }
    return {
        "asset_id": "vinuni-campus-map",
        "title": "Bản đồ khuôn viên VinUniversity",
        "url": url,
        "local_path": "1_map.png",
        "alt_text": "Bản đồ các tòa nhà và phòng học VinUniversity",
    }


def _get_rendered_route_media_asset(
    rendered_path: Path,
    plan: RoutePlan,
) -> dict:
    relative_path = rendered_path.relative_to(
        config.KNOWLEDGE_BASE_RAW_DIR
    ).as_posix()
    source_meta = get_source_metadata("3_link_vi_tri.txt")
    return {
        "asset_id": rendered_path.stem,
        "title": (
            f"Đường đi từ {plan.origin_label} tới {plan.destination_label}"
        ),
        "url": (
            source_meta.get("public_url")
            or "https://vinuni.edu.vn/vi/visit-2/"
        ),
        "local_path": relative_path,
        "alt_text": (
            f"Tuyến đường từ {plan.origin_label} tới "
            f"{plan.destination_label}"
        ),
    }


def _deterministic_route_text(plan: RoutePlan) -> str:
    steps = "\n".join(
        f"{index}. {step}" for index, step in enumerate(plan.steps, start=1)
    )
    return (
        f"Từ {plan.origin_label} tới {plan.destination_label}, "
        f"bạn đi theo tuyến sau:\n{steps}"
    )


def generate_vision_directions(question: str, origin: str, destination: str) -> dict:
    """Plan once, then produce grounded text and a deterministic route image."""
    try:
        plan = plan_route(origin, destination)
    except (UnknownLandmarkError, RouteNotFoundError):
        return {
            "answer": (
                "Mình chưa xác định được đầy đủ điểm xuất phát hoặc điểm đến "
                "trên bản đồ đã kiểm chứng. Bạn vui lòng làm rõ tên tòa nhà, "
                "cổng hoặc địa điểm được ghi trên bản đồ nhé."
            ),
            "sources": [],
            "has_evidence": False,
            "media": [get_map_media_asset()],
        }

    route_media = None
    try:
        route_media = _get_rendered_route_media_asset(
            render_route_map(plan),
            plan,
        )
    except OSError:
        route_media = None

    user_prompt = build_route_directions_prompt(question, plan)
    try:
        raw_answer = generate_text(
            ROUTE_DIRECTIONS_SYSTEM_PROMPT,
            user_prompt,
        )
    except LLMProviderError:
        raw_answer = _deterministic_route_text(plan)

    map_asset = get_map_media_asset()
    sources_text = f"\n\nNguồn tham khảo:\n- [{map_asset['title']}]({map_asset['url']})"
    full_answer = f"{raw_answer.rstrip()}{sources_text}"

    return {
        "answer": full_answer,
        "sources": [f"1_map.png#{plan.map_version}"],
        "has_evidence": True,
        "media": [route_media or map_asset],
    }
