from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.graph_types import (
    GraphBBox,
    GraphEdge,
    GraphMetadata,
    GraphNode,
    ValidatedGraph,
)

DEFAULT_GRAPH_PATH = Path(__file__).resolve().parents[1] / "data" / "road_graph.json"

BBOX_FIELDS = (
    "min_latitude",
    "min_longitude",
    "max_latitude",
    "max_longitude",
)


class GraphValidationError(ValueError):
    """Raised when graph JSON does not satisfy SPEC section 9 rules."""

def load_graph_data(path: Path | str = DEFAULT_GRAPH_PATH) -> ValidatedGraph:
    graph_path = Path(path)
    if not graph_path.is_file():
        raise GraphValidationError(f"Graph file not found: {graph_path}")

    try:
        raw = json.loads(graph_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GraphValidationError(f"Graph JSON is malformed: {graph_path}") from exc

    return validate_graph_data(raw)


def validate_graph_data(data: Any) -> ValidatedGraph:
    if not isinstance(data, dict):
        raise GraphValidationError("Graph root must be an object")

    metadata = _validate_metadata(data.get("metadata"))
    nodes = _validate_nodes(data.get("nodes"), metadata.bbox)
    edges = _validate_edges(data.get("edges"), nodes)

    return ValidatedGraph(metadata=metadata, nodes=nodes, edges=edges)


def _validate_metadata(metadata: Any) -> GraphMetadata:
    if not isinstance(metadata, dict):
        raise GraphValidationError("metadata is required")

    graph_version = metadata.get("graph_version")
    if not isinstance(graph_version, str) or not graph_version.strip():
        raise GraphValidationError("metadata.graph_version must be a non-empty string")

    bbox_values = _validate_bbox(metadata.get("bbox"))
    _validate_bbox_ranges(bbox_values)

    max_snap_distance = metadata.get("max_snap_distance_meters")
    if not isinstance(max_snap_distance, (int, float)) or float(max_snap_distance) <= 0:
        raise GraphValidationError("metadata.max_snap_distance_meters must be > 0")

    return GraphMetadata(
        graph_version=graph_version.strip(),
        bbox=GraphBBox(**bbox_values),
        max_snap_distance_meters=float(max_snap_distance),
    )


def _validate_bbox(bbox_raw: Any) -> dict[str, float]:
    if not isinstance(bbox_raw, dict):
        raise GraphValidationError("metadata.bbox is required")

    bbox_values: dict[str, float] = {}
    for field in BBOX_FIELDS:
        value = bbox_raw.get(field)
        if not isinstance(value, (int, float)):
            raise GraphValidationError(f"metadata.bbox.{field} must be numeric")
        bbox_values[field] = float(value)
    return bbox_values


def _validate_bbox_ranges(bbox_values: dict[str, float]) -> None:
    min_lat = bbox_values["min_latitude"]
    max_lat = bbox_values["max_latitude"]
    min_lon = bbox_values["min_longitude"]
    max_lon = bbox_values["max_longitude"]

    if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
        raise GraphValidationError("metadata.bbox latitude values must be between -90 and 90")
    if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
        raise GraphValidationError("metadata.bbox longitude values must be between -180 and 180")
    if min_lat > max_lat or min_lon > max_lon:
        raise GraphValidationError("metadata.bbox is inverted or malformed")


def _validate_nodes(nodes: Any, bbox: GraphBBox) -> dict[str, GraphNode]:
    if not isinstance(nodes, dict) or not nodes:
        raise GraphValidationError("nodes must be a non-empty object keyed by node ID")

    validated: dict[str, GraphNode] = {}
    for node_id, node in nodes.items():
        validated[node_id] = _validate_single_node(node_id, node, bbox, validated)

    return validated


def _validate_single_node(
    node_id: str,
    node: Any,
    bbox: GraphBBox,
    validated: dict[str, GraphNode],
) -> GraphNode:
    """Validate one node entry; raises on any structural violation."""
    _validate_node_id(node_id, validated)
    if not isinstance(node, dict):
        raise GraphValidationError(f"node {node_id} must be an object")

    latitude = node.get("latitude")
    longitude = node.get("longitude")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        raise GraphValidationError(f"node {node_id} must include numeric latitude and longitude")

    lat = float(latitude)
    lon = float(longitude)
    _validate_node_coordinates(node_id, lat, lon, bbox)
    return GraphNode(latitude=lat, longitude=lon)


def _validate_node_id(node_id: str, validated: dict[str, GraphNode]) -> None:
    """Validate the node ID itself (non-empty string, not duplicate)."""
    if not isinstance(node_id, str) or not node_id:
        raise GraphValidationError("node IDs must be non-empty strings")
    if node_id in validated:
        raise GraphValidationError(f"duplicate node ID: {node_id}")


def _validate_node_coordinates(
    node_id: str, lat: float, lon: float, bbox: GraphBBox
) -> None:
    """Validate that a node's coordinates are in range and inside the bbox."""
    if not -90 <= lat <= 90:
        raise GraphValidationError(f"node {node_id} latitude is invalid")
    if not -180 <= lon <= 180:
        raise GraphValidationError(f"node {node_id} longitude is invalid")
    if not _point_inside_bbox(lat, lon, bbox):
        raise GraphValidationError(f"node {node_id} is outside metadata bbox")


def _validate_edges(edges: Any, nodes: dict[str, GraphNode]) -> list[GraphEdge]:
    if not isinstance(edges, list):
        raise GraphValidationError("edges must be an array")

    return [
        _validate_single_edge(index, edge, nodes)
        for index, edge in enumerate(edges)
    ]


def _validate_single_edge(
    index: int,
    edge: Any,
    nodes: dict[str, GraphNode],
) -> GraphEdge:
    if not isinstance(edge, dict):
        raise GraphValidationError(f"edge at index {index} must be an object")

    from_node = edge.get("from")
    to_node = edge.get("to")
    distance = edge.get("distance")

    _validate_edge_endpoint(index, "from", from_node, nodes)
    _validate_edge_endpoint(index, "to", to_node, nodes)
    _validate_edge_distance(index, distance)

    return GraphEdge(
        from_node=from_node,
        to_node=to_node,
        distance=float(distance),
        oneway=bool(edge.get("oneway", False)),
        road_type=str(edge.get("road_type", "default")),
    )


def _validate_edge_endpoint(
    index: int,
    field: str,
    node_id: Any,
    nodes: dict[str, GraphNode],
) -> None:
    if not isinstance(node_id, str) or not node_id:
        raise GraphValidationError(f"edge at index {index} must include {field}")
    if node_id not in nodes:
        raise GraphValidationError(f"edge at index {index} references missing node")


def _validate_edge_distance(index: int, distance: Any) -> None:
    if not isinstance(distance, (int, float)) or float(distance) <= 0:
        raise GraphValidationError(f"edge at index {index} distance must be > 0")


def _point_inside_bbox(latitude: float, longitude: float, bbox: GraphBBox) -> bool:
    return (
        bbox.min_latitude <= latitude <= bbox.max_latitude
        and bbox.min_longitude <= longitude <= bbox.max_longitude
    )
