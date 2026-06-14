from __future__ import annotations

from dataclasses import dataclass

from app.application.graph_runtime import GraphRuntime, _options_hash
from app.domain.cost_model import RoutingOptions
from app.domain.dijkstra import bidirectional_dijkstra
from app.domain.errors import NoRouteError
from app.domain.snapper import snap_point


@dataclass(frozen=True)
class CostMatrixEntry:
    distance_meters: float
    path_node_ids: list[str]


class CostMatrix:
    """Many-to-many distance matrix using Dijkstra from each source.

    Caches results by (graph_version, options_hash, src_node, dst_node).
    """

    def __init__(self, runtime: GraphRuntime, options: RoutingOptions | None = None):
        if options is None:
            options = RoutingOptions()
        self._runtime = runtime
        self._options = options
        self._opts_hash = _options_hash(options)
        self._entries: dict[tuple[str, str], CostMatrixEntry] = {}

    def get_distance(self, src_node: str, dst_node: str) -> float | None:
        entry = self._get_entry(src_node, dst_node)
        return entry.distance_meters if entry else None

    def get_path(self, src_node: str, dst_node: str) -> list[str] | None:
        entry = self._get_entry(src_node, dst_node)
        return entry.path_node_ids if entry else None

    def _get_entry(self, src_node: str, dst_node: str) -> CostMatrixEntry | None:
        key = (src_node, dst_node)
        if key in self._entries:
            return self._entries[key]

        return None

    def compute_for_nodes(self, node_ids: list[str]) -> None:
        """Pre-compute distances between all pairs of given nodes."""
        adjacency = self._runtime.adjacency_for(self._options)
        version = self._runtime.metadata.graph_version
        cache = self._runtime.route_cache

        for src in node_ids:
            for dst in node_ids:
                if src == dst:
                    self._entries[(src, dst)] = CostMatrixEntry(
                        distance_meters=0.0, path_node_ids=[src]
                    )
                    continue

                # Check route cache first
                cached = cache.get(version, self._opts_hash, src, dst)
                if cached is not None:
                    self._entries[(src, dst)] = CostMatrixEntry(
                        distance_meters=cached.graph_distance_meters,
                        path_node_ids=list(cached.node_ids),
                    )
                    continue

                try:
                    result = bidirectional_dijkstra(adjacency, src, dst)
                    entry = CostMatrixEntry(
                        distance_meters=result.graph_distance_meters,
                        path_node_ids=list(result.node_ids),
                    )
                    self._entries[(src, dst)] = entry
                except NoRouteError:
                    self._entries[(src, dst)] = CostMatrixEntry(
                        distance_meters=float("inf"),
                        path_node_ids=[],
                    )

    def snap_points(
        self, coordinates: list[tuple[float, float]]
    ) -> list[str]:
        """Snap coordinates to node IDs, returning list of node IDs."""
        node_ids = []
        for lat, lon in coordinates:
            snap = snap_point(self._runtime, lat, lon)
            node_ids.append(snap.node_id)
        return node_ids
