from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.domain.graph import Adjacency, build_bidirectional_adjacency
from app.infrastructure.graph_loader import (
    DEFAULT_GRAPH_PATH,
    GraphMetadata,
    GraphNode,
    GraphEdge,
    load_graph_data,
)
from app.infrastructure.grid_index import GridSpatialIndex
from app.infrastructure.route_cache import RouteCache


@dataclass(frozen=True)
class GraphRuntime:
    metadata: GraphMetadata
    nodes: dict[str, GraphNode]
    edges: list[GraphEdge]
    adjacency: Adjacency
    grid_index: GridSpatialIndex
    route_cache: RouteCache

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)


def build_graph_runtime(path: Path | str | None = None) -> GraphRuntime:
    graph_path = Path(path) if path is not None else DEFAULT_GRAPH_PATH
    validated = load_graph_data(graph_path)
    adjacency = build_bidirectional_adjacency(validated)
    grid_index = GridSpatialIndex(validated.nodes, validated.metadata.bbox)
    route_cache = RouteCache()

    return GraphRuntime(
        metadata=validated.metadata,
        nodes=validated.nodes,
        edges=validated.edges,
        adjacency=adjacency,
        grid_index=grid_index,
        route_cache=route_cache,
    )
