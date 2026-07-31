"""Verified campus route graph and deterministic shortest-path planner."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import heapq
import json
import math
from pathlib import Path
import re
import unicodedata


_GRAPH_PATH = Path(__file__).with_name("campus_route_graph.json")


class UnknownLandmarkError(ValueError):
    """Raised when a user location is not represented by the verified graph."""


class RouteNotFoundError(ValueError):
    """Raised when two verified landmarks have no connected route."""


@dataclass(frozen=True)
class RouteNode:
    node_id: str
    label: str
    point: tuple[int, int]
    aliases: tuple[str, ...]
    landmark: bool


@dataclass(frozen=True)
class RouteEdge:
    source: str
    target: str
    points: tuple[tuple[int, int], ...]
    instruction: str
    cost: float


@dataclass(frozen=True)
class RoutePlan:
    map_version: str
    map_filename: str
    origin_id: str
    origin_label: str
    destination_id: str
    destination_label: str
    node_ids: tuple[str, ...]
    points: tuple[tuple[int, int], ...]
    steps: tuple[str, ...]


@dataclass(frozen=True)
class RouteGraph:
    version: str
    map_filename: str
    width: int
    height: int
    nodes: dict[str, RouteNode]
    edges: tuple[RouteEdge, ...]
    aliases: dict[str, str]

    def resolve(self, query: str) -> str:
        normalized = _normalize_alias(query)
        exact = self.aliases.get(normalized)
        if exact:
            return exact

        matches = [
            (len(alias), node_id)
            for alias, node_id in self.aliases.items()
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized)
        ]
        if not matches:
            raise UnknownLandmarkError(
                f"Địa điểm chưa có trong bản đồ đã xác minh: {query}"
            )
        matches.sort(reverse=True)
        return matches[0][1]


def _normalize_alias(value: str) -> str:
    value = value.casefold().replace("đ", "d")
    value = "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if unicodedata.category(character) != "Mn"
    )
    value = re.sub(r"[^\w\s-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _polyline_cost(points: tuple[tuple[int, int], ...]) -> float:
    return sum(
        math.dist(points[index - 1], points[index])
        for index in range(1, len(points))
    )


def validate_route_graph(data: dict) -> None:
    map_data = data.get("map", {})
    width = int(map_data.get("width", 0))
    height = int(map_data.get("height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("Route graph map dimensions must be positive")

    nodes = data.get("nodes", {})
    if not nodes:
        raise ValueError("Route graph must contain nodes")

    normalized_aliases: dict[str, str] = {}
    for node_id, node in nodes.items():
        point = node.get("point", [])
        if (
            len(point) != 2
            or not 0 <= point[0] < width
            or not 0 <= point[1] < height
        ):
            raise ValueError(f"Node outside map bounds: {node_id}")
        for alias in [node.get("label", ""), *node.get("aliases", [])]:
            normalized = _normalize_alias(alias)
            if not normalized:
                continue
            owner = normalized_aliases.get(normalized)
            if owner is not None and owner != node_id:
                raise ValueError(f"Duplicate route alias: {alias}")
            normalized_aliases[normalized] = node_id

    adjacency = {node_id: set() for node_id in nodes}
    for edge in data.get("edges", []):
        source = edge.get("from")
        target = edge.get("to")
        if source not in nodes or target not in nodes:
            raise ValueError(f"Edge references unknown node: {source} -> {target}")
        points = edge.get("points", [])
        if len(points) < 2:
            raise ValueError(f"Edge requires at least two points: {source} -> {target}")
        if points[0] != nodes[source]["point"] or points[-1] != nodes[target]["point"]:
            raise ValueError(f"Edge endpoints do not match nodes: {source} -> {target}")
        if any(
            len(point) != 2
            or not 0 <= point[0] < width
            or not 0 <= point[1] < height
            for point in points
        ):
            raise ValueError(f"Edge point outside map bounds: {source} -> {target}")
        adjacency[source].add(target)
        adjacency[target].add(source)

    landmark_ids = {
        node_id for node_id, node in nodes.items() if node.get("landmark", False)
    }
    start = next(iter(landmark_ids))
    visited = {start}
    pending = [start]
    while pending:
        current = pending.pop()
        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                pending.append(neighbor)
    if not landmark_ids.issubset(visited):
        raise ValueError("All landmark nodes must belong to one connected graph")


@lru_cache(maxsize=1)
def load_route_graph(path: Path | None = None) -> RouteGraph:
    graph_path = path or _GRAPH_PATH
    with open(graph_path, encoding="utf-8") as graph_file:
        data = json.load(graph_file)
    validate_route_graph(data)

    nodes = {
        node_id: RouteNode(
            node_id=node_id,
            label=node["label"],
            point=tuple(node["point"]),
            aliases=tuple(node.get("aliases", [])),
            landmark=bool(node.get("landmark", False)),
        )
        for node_id, node in data["nodes"].items()
    }
    aliases = {}
    for node in nodes.values():
        if not node.landmark:
            continue
        for alias in (node.label, *node.aliases):
            aliases[_normalize_alias(alias)] = node.node_id

    edges = []
    for edge in data["edges"]:
        points = tuple(tuple(point) for point in edge["points"])
        edges.append(
            RouteEdge(
                source=edge["from"],
                target=edge["to"],
                points=points,
                instruction=edge["instruction"],
                cost=_polyline_cost(points),
            )
        )

    return RouteGraph(
        version=data["version"],
        map_filename=data["map"]["filename"],
        width=data["map"]["width"],
        height=data["map"]["height"],
        nodes=nodes,
        edges=tuple(edges),
        aliases=aliases,
    )


def plan_route(origin: str, destination: str) -> RoutePlan:
    graph = load_route_graph()
    origin_id = graph.resolve(origin)
    destination_id = graph.resolve(destination)
    if (
        origin_id == destination_id
        and _normalize_alias(destination) not in graph.aliases
    ):
        raise UnknownLandmarkError(
            f"Địa điểm chưa có trong bản đồ đã xác minh: {destination}"
        )
    if origin_id == destination_id:
        node = graph.nodes[origin_id]
        return RoutePlan(
            map_version=graph.version,
            map_filename=graph.map_filename,
            origin_id=origin_id,
            origin_label=node.label,
            destination_id=destination_id,
            destination_label=node.label,
            node_ids=(origin_id,),
            points=(node.point,),
            steps=(f"Bạn đã ở {node.label}.",),
        )

    adjacency: dict[str, list[tuple[str, RouteEdge]]] = {
        node_id: [] for node_id in graph.nodes
    }
    for edge in graph.edges:
        adjacency[edge.source].append((edge.target, edge))
        adjacency[edge.target].append((edge.source, edge))

    distances = {origin_id: 0.0}
    previous: dict[str, tuple[str, RouteEdge]] = {}
    pending = [(0.0, origin_id)]
    while pending:
        distance, current = heapq.heappop(pending)
        if distance != distances.get(current):
            continue
        if current == destination_id:
            break
        for neighbor, edge in adjacency[current]:
            candidate = distance + edge.cost
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                previous[neighbor] = (current, edge)
                heapq.heappush(pending, (candidate, neighbor))

    if destination_id not in previous:
        raise RouteNotFoundError(
            f"Không có tuyến đã xác minh từ {origin} tới {destination}"
        )

    segments: list[tuple[str, str, RouteEdge]] = []
    current = destination_id
    while current != origin_id:
        parent, edge = previous[current]
        segments.append((parent, current, edge))
        current = parent
    segments.reverse()

    node_ids = [origin_id]
    route_points: list[tuple[int, int]] = []
    steps = []
    for source, target, edge in segments:
        oriented_points = (
            edge.points if edge.source == source else tuple(reversed(edge.points))
        )
        route_points.extend(
            oriented_points if not route_points else oriented_points[1:]
        )
        node_ids.append(target)
        source_label = graph.nodes[source].label
        target_label = graph.nodes[target].label
        if edge.source == source:
            instruction = edge.instruction[:1].lower() + edge.instruction[1:]
            steps.append(f"Từ {source_label}, {instruction}")
        else:
            steps.append(
                f"Từ {source_label}, đi theo lối đã đánh dấu tới "
                f"{target_label}."
            )

    return RoutePlan(
        map_version=graph.version,
        map_filename=graph.map_filename,
        origin_id=origin_id,
        origin_label=graph.nodes[origin_id].label,
        destination_id=destination_id,
        destination_label=graph.nodes[destination_id].label,
        node_ids=tuple(node_ids),
        points=tuple(route_points),
        steps=tuple(steps),
    )
