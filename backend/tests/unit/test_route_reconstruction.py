from pathlib import Path

import pytest

from app.application.graph_runtime import build_graph_runtime
from app.application.node_lookup import GraphNodeLookup
from app.domain.dijkstra import bidirectional_dijkstra
from app.domain.route_reconstruction import (
    RouteCoordinate,
    compute_total_distance_meters,
    dedupe_adjacent_exact_coordinates,
    reconstruct_route_points,
)
from app.application.snap_service import snap_point

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


@pytest.fixture
def runtime():
    return build_graph_runtime(FIXTURE_GRAPH_PATH)


def _coord(lat: float, lon: float) -> RouteCoordinate:
    return RouteCoordinate(latitude=lat, longitude=lon)


def test_route_points_begin_with_clicked_start_and_end_with_clicked_end(runtime):
    start = (10.7785, 106.7149)
    end = (10.7808, 106.7172)
    start_snap = snap_point(runtime, start[0], start[1])
    end_snap = snap_point(runtime, end[0], end[1])
    dijkstra = bidirectional_dijkstra(
        runtime.adjacency, start_snap.node_id, end_snap.node_id
    )
    route = reconstruct_route_points(
        GraphNodeLookup(runtime.nodes),
        clicked_start=start,
        clicked_end=end,
        start_snap_distance_meters=start_snap.distance_meters,
        end_snap_distance_meters=end_snap.distance_meters,
        dijkstra_node_ids=dijkstra.node_ids,
        graph_distance_meters=dijkstra.graph_distance_meters,
    )
    assert route[0].latitude == pytest.approx(start[0])
    assert route[0].longitude == pytest.approx(start[1])
    assert route[-1].latitude == pytest.approx(end[0])
    assert route[-1].longitude == pytest.approx(end[1])


def test_intermediate_points_follow_dijkstra_node_order(runtime):
    start = (10.7785, 106.7149)
    end = (10.7808, 106.7172)
    start_snap = snap_point(runtime, start[0], start[1])
    end_snap = snap_point(runtime, end[0], end[1])
    dijkstra = bidirectional_dijkstra(
        runtime.adjacency, start_snap.node_id, end_snap.node_id
    )
    route = reconstruct_route_points(
        GraphNodeLookup(runtime.nodes),
        clicked_start=start,
        clicked_end=end,
        start_snap_distance_meters=start_snap.distance_meters,
        end_snap_distance_meters=end_snap.distance_meters,
        dijkstra_node_ids=dijkstra.node_ids,
        graph_distance_meters=dijkstra.graph_distance_meters,
    )
    mid = runtime.nodes["node-mid"]
    assert any(
        p.latitude == pytest.approx(mid.latitude)
        and p.longitude == pytest.approx(mid.longitude)
        for p in route[1:-1]
    )
    assert dijkstra.node_ids == ["node-start", "node-mid", "node-end"]


def test_exact_endpoint_on_node_dedupes_adjacent_duplicate(runtime):
    node = runtime.nodes["node-start"]
    start = (node.latitude, node.longitude)
    end = (10.7808, 106.7172)
    start_snap = snap_point(runtime, start[0], start[1])
    end_snap = snap_point(runtime, end[0], end[1])
    dijkstra = bidirectional_dijkstra(
        runtime.adjacency, start_snap.node_id, end_snap.node_id
    )
    route = reconstruct_route_points(
        GraphNodeLookup(runtime.nodes),
        clicked_start=start,
        clicked_end=end,
        start_snap_distance_meters=start_snap.distance_meters,
        end_snap_distance_meters=end_snap.distance_meters,
        dijkstra_node_ids=dijkstra.node_ids,
        graph_distance_meters=dijkstra.graph_distance_meters,
    )
    assert route[0].latitude == pytest.approx(start[0])
    assert not _has_adjacent_duplicate(route)


def test_non_identical_snap_segment_preserved_when_offset_from_node(runtime):
    start = (10.7785, 106.7149)
    end = (10.7808, 106.7172)
    start_snap = snap_point(runtime, start[0], start[1])
    end_snap = snap_point(runtime, end[0], end[1])
    assert start_snap.distance_meters > 0.0
    dijkstra = bidirectional_dijkstra(
        runtime.adjacency, start_snap.node_id, end_snap.node_id
    )
    route = reconstruct_route_points(
        GraphNodeLookup(runtime.nodes),
        clicked_start=start,
        clicked_end=end,
        start_snap_distance_meters=start_snap.distance_meters,
        end_snap_distance_meters=end_snap.distance_meters,
        dijkstra_node_ids=dijkstra.node_ids,
        graph_distance_meters=dijkstra.graph_distance_meters,
    )
    assert len(route) >= 3
    assert route[0].latitude == pytest.approx(start[0])


def test_distance_matches_independent_fixture_calculation(runtime):
    start = (10.7785, 106.7149)
    end = (10.7808, 106.7172)
    start_snap = snap_point(runtime, start[0], start[1])
    end_snap = snap_point(runtime, end[0], end[1])
    dijkstra = bidirectional_dijkstra(
        runtime.adjacency, start_snap.node_id, end_snap.node_id
    )
    distance = compute_total_distance_meters(
        start_snap_distance_meters=start_snap.distance_meters,
        end_snap_distance_meters=end_snap.distance_meters,
        graph_distance_meters=dijkstra.graph_distance_meters,
    )
    expected = (
        start_snap.distance_meters
        + dijkstra.graph_distance_meters
        + end_snap.distance_meters
    )
    assert distance == pytest.approx(expected, rel=1e-9, abs=1e-6)


def test_same_snapped_node_returns_snap_only_route(runtime):
    lat, lon = 10.77925, 106.71555
    start = (lat, lon)
    end = (lat + 0.00005, lon + 0.00005)
    start_snap = snap_point(runtime, start[0], start[1])
    end_snap = snap_point(runtime, end[0], end[1])
    assert start_snap.node_id == end_snap.node_id == "node-mid"
    dijkstra = bidirectional_dijkstra(
        runtime.adjacency, start_snap.node_id, end_snap.node_id
    )
    assert dijkstra.node_ids == ["node-mid"]
    assert dijkstra.graph_distance_meters == pytest.approx(0.0)
    route = reconstruct_route_points(
        GraphNodeLookup(runtime.nodes),
        clicked_start=start,
        clicked_end=end,
        start_snap_distance_meters=start_snap.distance_meters,
        end_snap_distance_meters=end_snap.distance_meters,
        dijkstra_node_ids=dijkstra.node_ids,
        graph_distance_meters=dijkstra.graph_distance_meters,
    )
    assert route[0].latitude == pytest.approx(start[0])
    assert route[-1].latitude == pytest.approx(end[0])
    distance = compute_total_distance_meters(
        start_snap.distance_meters,
        end_snap.distance_meters,
        dijkstra.graph_distance_meters,
    )
    assert distance == pytest.approx(
        start_snap.distance_meters + end_snap.distance_meters, rel=1e-9
    )
    for _ in range(10):
        again = reconstruct_route_points(
            GraphNodeLookup(runtime.nodes),
            clicked_start=start,
            clicked_end=end,
            start_snap_distance_meters=start_snap.distance_meters,
            end_snap_distance_meters=end_snap.distance_meters,
            dijkstra_node_ids=dijkstra.node_ids,
            graph_distance_meters=dijkstra.graph_distance_meters,
        )
        assert [(p.latitude, p.longitude) for p in again] == [
            (p.latitude, p.longitude) for p in route
        ]


def test_dedupe_adjacent_exact_coordinates_only():
    raw = [
        _coord(1.0, 1.0),
        _coord(1.0, 1.0),
        _coord(2.0, 2.0),
        _coord(3.0, 3.0),
        _coord(3.0, 3.0),
    ]
    deduped = dedupe_adjacent_exact_coordinates(raw)
    assert len(deduped) == 3
    assert deduped[0].latitude == 1.0
    assert deduped[1].latitude == 2.0
    assert deduped[2].latitude == 3.0


def _has_adjacent_duplicate(route: list[RouteCoordinate]) -> bool:
    for i in range(1, len(route)):
        a, b = route[i - 1], route[i]
        if (
            abs(a.latitude - b.latitude) <= 1e-9
            and abs(a.longitude - b.longitude) <= 1e-9
        ):
            return True
    return False
