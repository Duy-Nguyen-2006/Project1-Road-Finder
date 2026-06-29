from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path

from app.domain.cost_model import RoutingOptions
from app.domain.graph import Adjacency, build_directed_adjacency, build_reverse_adjacency
from app.domain.graph_types import GraphEdge, GraphMetadata, GraphNode, ValidatedGraph
from app.infrastructure.graph_loader import DEFAULT_GRAPH_PATH, load_graph_data
from app.infrastructure.grid_index import GridSpatialIndex
from app.infrastructure.route_cache import RouteCache


def _options_hash(options: RoutingOptions) -> str:
    return f"{sorted(options.avoid_road_types)}|{sorted(options.avoid_edge_ids)}"


@dataclass(frozen=True)
class GraphRuntime:
    metadata: GraphMetadata
    nodes: dict[str, GraphNode]
    edges: list[GraphEdge]
    base_adjacency: Adjacency
    grid_index: GridSpatialIndex
    route_cache: RouteCache
    _adjacency_cache: dict[str, Adjacency] = field(default_factory=dict)
    _reverse_adjacency_cache: dict[str, Adjacency] = field(default_factory=dict)
    _adjacency_lock: threading.Lock = field(
        default_factory=threading.Lock, compare=False, repr=False
    )

    def _ensure_adjacency(self, options: RoutingOptions) -> None:
        key = _options_hash(options)
        if key in self._adjacency_cache and key in self._reverse_adjacency_cache:
            return

        with self._adjacency_lock:
            if key in self._adjacency_cache and key in self._reverse_adjacency_cache:
                return
            validated = ValidatedGraph(
                metadata=self.metadata, nodes=self.nodes, edges=self.edges
            )
            forward = build_directed_adjacency(validated, options)
            self._adjacency_cache[key] = forward
            self._reverse_adjacency_cache[key] = build_reverse_adjacency(forward)

    def adjacency_for(self, options: RoutingOptions | None = None) -> Adjacency:
        if options is None:
            options = RoutingOptions()
        self._ensure_adjacency(options)
        return self._adjacency_cache[_options_hash(options)]

    def reverse_adjacency_for(self, options: RoutingOptions | None = None) -> Adjacency:
        if options is None:
            options = RoutingOptions()
        self._ensure_adjacency(options)
        return self._reverse_adjacency_cache[_options_hash(options)]

    @property
    def adjacency(self) -> Adjacency:
        return self.base_adjacency

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)


def build_graph_runtime(path: Path | str | None = None) -> GraphRuntime:
    graph_path = Path(path) if path is not None else DEFAULT_GRAPH_PATH
    validated = load_graph_data(graph_path)
    adjacency = build_directed_adjacency(validated)
    grid_index = GridSpatialIndex(validated.nodes, validated.metadata.bbox)
    route_cache = RouteCache()

    return GraphRuntime(
        metadata=validated.metadata,
        nodes=validated.nodes,
        edges=validated.edges,
        base_adjacency=adjacency,
        grid_index=grid_index,
        route_cache=route_cache,
    )