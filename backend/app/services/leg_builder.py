from __future__ import annotations

from app.application.node_lookup import GraphNodeLookup
from app.domain.route_reconstruction import (
    compute_total_distance_meters,
    reconstruct_route_points,
)
from app.models.point import Point


def leg_route_points_and_distance(
    lookup: GraphNodeLookup,
    *,
    clicked_start: tuple[float, float],
    clicked_end: tuple[float, float],
    start_snap_distance_meters: float,
    end_snap_distance_meters: float,
    path_node_ids: list[str],
    graph_distance_meters: float,
) -> tuple[list[Point], float]:
    coords = reconstruct_route_points(
        lookup,
        clicked_start=clicked_start,
        clicked_end=clicked_end,
        dijkstra_node_ids=path_node_ids,
    )
    distance = compute_total_distance_meters(
        start_snap_distance_meters,
        end_snap_distance_meters,
        graph_distance_meters,
    )
    points = [
        Point(latitude=c.latitude, longitude=c.longitude) for c in coords
    ]
    return points, distance
