from __future__ import annotations

from dataclasses import dataclass

from app.application.graph_runtime import GraphRuntime, _options_hash
from app.domain.cost_model import RoutingOptions
from app.domain.dijkstra import bidirectional_dijkstra
from app.domain.errors import NoRouteError
from app.application.snap_service import snap_point
from app.infrastructure.route_cache import CachedGraphPath


@dataclass(frozen=True)
class CostMatrixEntry:
    distance_meters: float
    path_node_ids: tuple[str, ...]


class CostMatrix:
    """Many-to-many distance matrix using Dijkstra from each source.

    Caches results by (graph_version, options_hash, src_node, dst_node).
    Pair lookups compute on demand when not yet precomputed.
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
        return entry.distance_meters

    def get_path(self, src_node: str, dst_node: str) -> list[str] | None:
        entry = self._get_entry(src_node, dst_node)
        return list(entry.path_node_ids)

    def _get_entry(self, src_node: str, dst_node: str) -> CostMatrixEntry:
        key = (src_node, dst_node)
        if key not in self._entries:
            self._entries[key] = self._compute_pair(src_node, dst_node)
        return self._entries[key]

    def _compute_pair(self, src_node: str, dst_node: str) -> CostMatrixEntry:
        if src_node == dst_node:
            return CostMatrixEntry(distance_meters=0.0, path_node_ids=(src_node,))

        version = self._runtime.metadata.graph_version
        cache = self._runtime.route_cache
        cached = cache.get(version, self._opts_hash, src_node, dst_node)
        if cached is not None:
            return CostMatrixEntry(
                distance_meters=cached.graph_distance_meters,
                path_node_ids=tuple(cached.node_ids),
            )

        adjacency = self._runtime.adjacency_for(self._options)
        reverse_adjacency = self._runtime.reverse_adjacency_for(self._options)
        try:
            result = bidirectional_dijkstra(
                adjacency, src_node, dst_node, reverse_adjacency=reverse_adjacency
            )
            path = CachedGraphPath(
                node_ids=list(result.node_ids),
                graph_distance_meters=result.graph_distance_meters,
            )
            cache.put(version, self._opts_hash, src_node, dst_node, path)
            return CostMatrixEntry(
                distance_meters=result.graph_distance_meters,
                path_node_ids=tuple(result.node_ids),
            )
        except NoRouteError:
            return CostMatrixEntry(distance_meters=float("inf"), path_node_ids=())

    def compute_for_nodes(self, node_ids: list[str]) -> None:
        """Pre-compute distances between all pairs of given nodes."""
        for src in node_ids:
            for dst in node_ids:
                self._get_entry(src, dst)

    def snap_points(
        self, coordinates: list[tuple[float, float]]
    ) -> list[str]:
        """Snap coordinates to node IDs, returning list of node IDs."""
        node_ids = []
        for lat, lon in coordinates:
            snap = snap_point(self._runtime, lat, lon)
            node_ids.append(snap.node_id)
        return node_ids