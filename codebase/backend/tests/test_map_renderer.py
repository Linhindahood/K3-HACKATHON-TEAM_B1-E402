"""Tests for deterministic route rendering and cache reuse."""
from __future__ import annotations

import time

from PIL import Image

from backend import config
from backend.rag.map_renderer import render_route_map
from backend.rag.route_graph import RoutePlan, plan_route


def _route_plan() -> RoutePlan:
    return RoutePlan(
        map_version="test-map-v1",
        map_filename="map.png",
        origin_id="origin",
        origin_label="Điểm đầu",
        destination_id="destination",
        destination_label="Điểm cuối",
        node_ids=("origin", "junction", "destination"),
        points=((20, 100), (100, 100), (180, 100)),
        steps=("Đi thẳng từ điểm đầu tới điểm cuối.",),
    )


def test_render_route_map_draws_line_and_distinct_markers(tmp_path):
    map_path = tmp_path / "map.png"
    Image.new("RGB", (200, 200), "white").save(map_path)

    output_path = render_route_map(
        _route_plan(),
        map_path=map_path,
        output_dir=tmp_path / "generated",
    )

    rendered = Image.open(output_path).convert("RGB")
    assert output_path.suffix == ".png"
    assert rendered.getpixel((100, 100)) != (255, 255, 255)
    assert rendered.getpixel((20, 100)) != rendered.getpixel((180, 100))
    assert all(
        rendered.getpixel((x, y)) == (255, 255, 255)
        for x in range(40, 90)
        for y in range(80, 96)
    )


def test_render_route_map_reuses_cached_png_without_rewriting(tmp_path):
    map_path = tmp_path / "map.png"
    Image.new("RGB", (200, 200), "white").save(map_path)
    output_dir = tmp_path / "generated"

    first = render_route_map(
        _route_plan(),
        map_path=map_path,
        output_dir=output_dir,
    )
    first_mtime = first.stat().st_mtime_ns
    second = render_route_map(
        _route_plan(),
        map_path=map_path,
        output_dir=output_dir,
    )

    assert second == first
    assert second.stat().st_mtime_ns == first_mtime


def test_cold_render_of_production_map_completes_under_one_second(tmp_path):
    plan = plan_route("tòa E", "tòa A")
    map_path = config.KNOWLEDGE_BASE_RAW_DIR / "1_map.png"

    started = time.perf_counter()
    render_route_map(
        plan,
        map_path=map_path,
        output_dir=tmp_path / "generated",
    )
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0
