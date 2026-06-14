from __future__ import annotations

from dataclasses import dataclass

from app.application.graph_runtime import GraphRuntime
from app.application.node_lookup import GraphNodeLookup
from app.domain.cost_model import RoutingOptions
from app.domain.route_reconstruction import reconstruct_route
from app.models.point import Point
from app.services.shortest_path_service import find_cached_or_compute_graph_path


@dataclass(frozen=True)
class ComputedRoute:
    route_points: list[Point]
    distance: float


def compute_shortest_path_response(
    runtime: GraphRuntime,
    start: Point,
    end: Point,
    options: RoutingOptions | None = None,
) -> ComputedRoute:
    graph_result = find_cached_or_compute_graph_path(
        runtime,
        (start.latitude, start.longitude),
        (end.latitude, end.longitude),
        options,
    )
    lookup = GraphNodeLookup(runtime.nodes)
    reconstructed = reconstruct_route(
        lookup,
        clicked_start=(start.latitude, start.longitude),
        clicked_end=(end.latitude, end.longitude),
        start_snap_distance_meters=graph_result.start_snap_distance_meters,
        end_snap_distance_meters=graph_result.end_snap_distance_meters,
        dijkstra_node_ids=list(graph_result.graph_path.node_ids),
        graph_distance_meters=graph_result.graph_path.graph_distance_meters,
    )
    route_points = [
        Point(latitude=p.latitude, longitude=p.longitude)
        for p in reconstructed.route_points
    ]
    return ComputedRoute(
        route_points=route_points,
        distance=reconstructed.distance_meters,
    )
