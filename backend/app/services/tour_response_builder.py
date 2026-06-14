from __future__ import annotations

from app.application.node_lookup import GraphNodeLookup
from app.domain.protocols import DistanceProvider
from app.domain.tsp import Stop
from app.models.point import Point
from app.models.route_models import LegResponse
from app.services.leg_builder import leg_route_points_and_distance


def build_tour_legs(
    lookup: GraphNodeLookup,
    *,
    shipper_click: tuple[float, float],
    shipper_snap_distance_meters: float,
    shipper_node_id: str,
    ordered_stops: list[Stop],
    stop_coordinates: dict[tuple[str, str], tuple[float, float]],
    stop_snap_distances: dict[tuple[str, str], float],
    cost_matrix: DistanceProvider,
) -> list[LegResponse]:
    """Build legs with snap-aware geometry like POST /route."""
    legs: list[LegResponse] = []
    current_node = shipper_node_id
    current_click = shipper_click
    current_snap_dist = shipper_snap_distance_meters

    for stop in ordered_stops:
        end_click = stop_coordinates[(stop.order_id, stop.kind)]
        graph_dist = cost_matrix.get_distance(current_node, stop.node_id)
        path = cost_matrix.get_path(current_node, stop.node_id) or []
        if graph_dist is None or graph_dist == float("inf"):
            legs.append(
                LegResponse(
                    kind=f"{stop.order_id}_{stop.kind}",
                    distance_meters=0.0,
                    route_points=[],
                )
            )
            current_node = stop.node_id
            current_click = end_click
            current_snap_dist = 0.0
            continue

        end_snap = stop_snap_distances.get((stop.order_id, stop.kind), 0.0)
        route_points, distance = leg_route_points_and_distance(
            lookup,
            clicked_start=current_click,
            clicked_end=end_click,
            start_snap_distance_meters=current_snap_dist,
            end_snap_distance_meters=end_snap,
            path_node_ids=path,
            graph_distance_meters=graph_dist,
        )
        legs.append(
            LegResponse(
                kind=f"{stop.order_id}_{stop.kind}",
                distance_meters=distance,
                route_points=route_points,
            )
        )
        current_node = stop.node_id
        current_click = end_click
        current_snap_dist = end_snap

    return legs


def build_assignment_leg(
    lookup: GraphNodeLookup,
    *,
    clicked_start: tuple[float, float],
    start_snap_distance_meters: float,
    clicked_end: tuple[float, float],
    end_snap_distance_meters: float,
    path_node_ids: list[str],
    graph_distance_meters: float,
    kind: str,
) -> LegResponse:
    route_points, distance = leg_route_points_and_distance(
        lookup,
        clicked_start=clicked_start,
        clicked_end=clicked_end,
        start_snap_distance_meters=start_snap_distance_meters,
        end_snap_distance_meters=end_snap_distance_meters,
        path_node_ids=path_node_ids,
        graph_distance_meters=graph_distance_meters,
    )
    return LegResponse(
        kind=kind,
        distance_meters=distance,
        route_points=route_points,
    )
