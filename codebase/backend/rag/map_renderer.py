"""Deterministic post-processing renderer for verified campus routes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile

from PIL import Image, ImageDraw, ImageFont

from backend import config
from backend.rag.route_graph import RoutePlan


_RENDERER_VERSION = "route-render-v2"


def _cache_name(plan: RoutePlan) -> str:
    payload = json.dumps(
        {
            "renderer_version": _RENDERER_VERSION,
            "map_version": plan.map_version,
            "node_ids": plan.node_ids,
            "points": plan.points,
        },
        ensure_ascii=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"route-{digest}.png"


def _draw_marker(
    draw: ImageDraw.ImageDraw,
    point: tuple[int, int],
    *,
    fill: str,
    label: str,
    radius: int,
    font: ImageFont.ImageFont,
) -> None:
    x, y = point
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill=fill,
        outline="white",
        width=max(2, radius // 4),
    )
    left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
    draw.text(
        (x - (right - left) / 2, y - (bottom - top) / 2 - top),
        label,
        fill="white",
        font=font,
    )


def render_route_map(
    plan: RoutePlan,
    map_path: Path | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Render and cache one verified route as a static PNG."""
    source_path = map_path or (
        config.KNOWLEDGE_BASE_RAW_DIR / plan.map_filename
    )
    destination_dir = output_dir or (
        config.KNOWLEDGE_BASE_RAW_DIR / "_generated"
    )
    destination_dir.mkdir(parents=True, exist_ok=True)
    output_path = destination_dir / _cache_name(plan)
    if output_path.exists():
        return output_path

    image = Image.open(source_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    line_width = max(6, image.width // 150)
    if len(plan.points) >= 2:
        draw.line(
            plan.points,
            fill="white",
            width=line_width + 6,
            joint="curve",
        )
        draw.line(
            plan.points,
            fill="#087fdb",
            width=line_width,
            joint="curve",
        )

    radius = max(10, image.width // 80)
    font = ImageFont.load_default(size=max(14, image.width // 65))
    _draw_marker(
        draw,
        plan.points[0],
        fill="#16a34a",
        label="S",
        radius=radius,
        font=font,
    )
    _draw_marker(
        draw,
        plan.points[-1],
        fill="#dc2626",
        label="D",
        radius=radius,
        font=font,
    )

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination_dir,
            prefix=".route-",
            suffix=".png",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        image.save(temporary_path, format="PNG")
        temporary_path.replace(output_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return output_path
