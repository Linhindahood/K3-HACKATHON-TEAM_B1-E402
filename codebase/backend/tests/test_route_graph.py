"""Tests for the verified campus route graph and deterministic planner."""
from __future__ import annotations

import pytest

from backend.rag.route_graph import (
    UnknownLandmarkError,
    load_route_graph,
    plan_route,
    validate_route_graph,
)


@pytest.mark.parametrize(
    ("query", "expected_id"),
    [
        ("tòa E", "building_e"),
        ("toa e", "building_e"),
        ("cổng đại lễ", "main_gate"),
    ],
)
def test_route_graph_resolves_verified_landmark_aliases(query, expected_id):
    graph = load_route_graph()

    assert graph.resolve(query) == expected_id


def test_plan_route_returns_one_shared_plan_for_text_and_renderer():
    plan = plan_route("tòa E", "tòa A")

    assert plan.origin_id == "building_e"
    assert plan.destination_id == "building_a"
    assert plan.node_ids[0] == "building_e"
    assert plan.node_ids[-1] == "building_a"
    assert len(plan.points) >= 2
    assert len(plan.steps) >= 1


def test_plan_route_steps_follow_the_actual_travel_direction():
    plan = plan_route("tòa E", "tòa A")

    assert plan.steps[0].startswith("Từ Tòa E")
    assert plan.steps[-1].endswith("Tòa A.")


def test_plan_route_does_not_guess_an_unverified_landmark():
    with pytest.raises(UnknownLandmarkError, match="bể bơi"):
        plan_route("tòa E", "bể bơi")


def test_plan_route_does_not_resolve_noisy_destination_back_to_origin():
    with pytest.raises(UnknownLandmarkError, match="bể bơi"):
        plan_route("tòa E", "vị trí bể bơi từ tòa E")


@pytest.mark.parametrize(
    "graph_data",
    [
        {
            "map": {"width": 100, "height": 100},
            "nodes": {
                "outside": {
                    "label": "Outside",
                    "point": [101, 50],
                    "aliases": ["outside"],
                    "landmark": True,
                }
            },
            "edges": [],
        },
        {
            "map": {"width": 100, "height": 100},
            "nodes": {
                "a": {
                    "label": "A",
                    "point": [10, 10],
                    "aliases": ["a"],
                    "landmark": True,
                }
            },
            "edges": [
                {
                    "from": "a",
                    "to": "missing",
                    "points": [[10, 10], [20, 20]],
                    "instruction": "Đi tới missing.",
                }
            ],
        },
        {
            "map": {"width": 100, "height": 100},
            "nodes": {
                "a": {
                    "label": "A",
                    "point": [10, 10],
                    "aliases": ["a"],
                    "landmark": True,
                },
                "b": {
                    "label": "B",
                    "point": [90, 90],
                    "aliases": ["b"],
                    "landmark": True,
                },
            },
            "edges": [],
        },
    ],
)
def test_validate_route_graph_rejects_invalid_or_disconnected_data(graph_data):
    with pytest.raises(ValueError):
        validate_route_graph(graph_data)
