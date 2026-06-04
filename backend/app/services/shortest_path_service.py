from __future__ import annotations

from dataclasses import dataclass

from app.application.graph_runtime import GraphRuntime
from app.domain.dijkstra import bidirectional_dijkstra
from app.domain.snapper import snap_point
from app.infrastructure.route_cache import CachedGraphPath


@dataclass(frozen=True)
class GraphPathResult:
    graph_path: CachedGraphPath
    start_node_id: str
    end_node_id: str
    start_snap_distance_meters: float
    end_snap_distance_meters: float
    from_cache: bool


def find_cached_or_compute_graph_path(
    runtime: GraphRuntime,
    clicked_start: tuple[float, float],
    clicked_end: tuple[float, float],
) -> GraphPathResult:
    start_snap = snap_point(runtime, clicked_start[0], clicked_start[1])
    end_snap = snap_point(runtime, clicked_end[0], clicked_end[1])
    version = runtime.metadata.graph_version

    cached = runtime.route_cache.get(
        version, start_snap.node_id, end_snap.node_id
    )
    if cached is not None:
        return GraphPathResult(
            graph_path=cached,
            start_node_id=start_snap.node_id,
            end_node_id=end_snap.node_id,
            start_snap_distance_meters=start_snap.distance_meters,
            end_snap_distance_meters=end_snap.distance_meters,
            from_cache=True,
        )

    dijkstra = bidirectional_dijkstra(
        runtime.adjacency, start_snap.node_id, end_snap.node_id
    )
    path = CachedGraphPath(
        node_ids=list(dijkstra.node_ids),
        graph_distance_meters=dijkstra.graph_distance_meters,
    )
    runtime.route_cache.put(
        version, start_snap.node_id, end_snap.node_id, path
    )
    return GraphPathResult(
        graph_path=path,
        start_node_id=start_snap.node_id,
        end_node_id=end_snap.node_id,
        start_snap_distance_meters=start_snap.distance_meters,
        end_snap_distance_meters=end_snap.distance_meters,
        from_cache=False,
    )
