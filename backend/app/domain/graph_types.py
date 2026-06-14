from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GraphBBox:
    min_latitude: float
    min_longitude: float
    max_latitude: float
    max_longitude: float


@dataclass(frozen=True)
class GraphMetadata:
    graph_version: str
    bbox: GraphBBox
    max_snap_distance_meters: float


@dataclass(frozen=True)
class GraphNode:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class GraphEdge:
    from_node: str
    to_node: str
    distance: float
    oneway: bool = False
    road_type: str = "default"


@dataclass(frozen=True)
class ValidatedGraph:
    metadata: GraphMetadata
    nodes: dict[str, GraphNode]
    edges: list[GraphEdge]
