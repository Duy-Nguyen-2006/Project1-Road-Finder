from __future__ import annotations

from dataclasses import dataclass

from app.domain.protocols import NodeCoordinateLookup

_COORD_TOLERANCE = 1e-9


@dataclass(frozen=True)
class RouteCoordinate:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class ReconstructedRoute:
    route_points: list[RouteCoordinate]
    distance_meters: float


def coordinates_equal(a: RouteCoordinate, b: RouteCoordinate) -> bool:
    return (
        abs(a.latitude - b.latitude) <= _COORD_TOLERANCE
        and abs(a.longitude - b.longitude) <= _COORD_TOLERANCE
    )


def dedupe_adjacent_exact_coordinates(
    points: list[RouteCoordinate],
) -> list[RouteCoordinate]:
    if not points:
        return []
    out: list[RouteCoordinate] = [points[0]]
    for p in points[1:]:
        if not coordinates_equal(out[-1], p):
            out.append(p)
    return out


def compute_total_distance_meters(
    start_snap_distance_meters: float,
    end_snap_distance_meters: float,
    graph_distance_meters: float,
) -> float:
    return (
        start_snap_distance_meters
        + graph_distance_meters
        + end_snap_distance_meters
    )


def reconstruct_route_points(
    lookup: NodeCoordinateLookup,
    *,
    clicked_start: tuple[float, float],
    clicked_end: tuple[float, float],
    dijkstra_node_ids: list[str],
) -> list[RouteCoordinate]:
    start_coord = RouteCoordinate(
        latitude=clicked_start[0], longitude=clicked_start[1]
    )
    end_coord = RouteCoordinate(latitude=clicked_end[0], longitude=clicked_end[1])

    graph_coords = [
        RouteCoordinate(latitude=lat, longitude=lon)
        for lat, lon in (lookup.node_coordinate(nid) for nid in dijkstra_node_ids)
    ]

    raw: list[RouteCoordinate] = [start_coord] + graph_coords + [end_coord]
    return dedupe_adjacent_exact_coordinates(raw)


def reconstruct_route(
    lookup: NodeCoordinateLookup,
    *,
    clicked_start: tuple[float, float],
    clicked_end: tuple[float, float],
    start_snap_distance_meters: float,
    end_snap_distance_meters: float,
    dijkstra_node_ids: list[str],
    graph_distance_meters: float,
) -> ReconstructedRoute:
    route_points = reconstruct_route_points(
        lookup,
        clicked_start=clicked_start,
        clicked_end=clicked_end,
        dijkstra_node_ids=dijkstra_node_ids,
    )
    distance_meters = compute_total_distance_meters(
        start_snap_distance_meters,
        end_snap_distance_meters,
        graph_distance_meters,
    )
    return ReconstructedRoute(
        route_points=route_points, distance_meters=distance_meters
    )
