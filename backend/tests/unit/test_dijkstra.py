import json
from pathlib import Path

import pytest

from app.application.graph_runtime import build_graph_runtime
from app.domain.dijkstra import bidirectional_dijkstra
from app.domain.errors import NoRouteError

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


@pytest.fixture
def runtime():
    return build_graph_runtime(FIXTURE_GRAPH_PATH)


def _write_graph(tmp_path: Path, nodes: dict, edges: list) -> Path:
    path = tmp_path / "graph.json"
    payload = {
        "metadata": {
            "graph_version": "dijkstra-test-v1",
            "bbox": {
                "min_latitude": 0.0,
                "min_longitude": 0.0,
                "max_latitude": 10.0,
                "max_longitude": 10.0,
            },
            "max_snap_distance_meters": 5000.0,
        },
        "nodes": nodes,
        "edges": edges,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_shortest_path_on_fixture_graph(runtime):
    result = bidirectional_dijkstra(
        runtime.adjacency, "node-start", "node-end"
    )
    assert result.node_ids == ["node-start", "node-mid", "node-end"]
    assert result.graph_distance_meters == pytest.approx(300.5)


def test_same_start_and_end_node_returns_zero_distance(runtime):
    result = bidirectional_dijkstra(
        runtime.adjacency, "node-mid", "node-mid"
    )
    assert result.node_ids == ["node-mid"]
    assert result.graph_distance_meters == pytest.approx(0.0)


def test_disconnected_component_raises_no_route(runtime):
    with pytest.raises(NoRouteError):
        bidirectional_dijkstra(runtime.adjacency, "node-start", "node-island")


def test_tie_break_prefers_lexicographically_smaller_neighbor_path(tmp_path):
    """Equal total cost: hub->a->end and hub->b->end; neighbors sorted by node id."""
    path = _write_graph(
        tmp_path,
        nodes={
            "hub": {"latitude": 1.0, "longitude": 1.0},
            "a": {"latitude": 1.1, "longitude": 1.0},
            "b": {"latitude": 1.2, "longitude": 1.0},
            "end": {"latitude": 2.0, "longitude": 1.0},
        },
        edges=[
            {"from": "hub", "to": "a", "distance": 10.0},
            {"from": "hub", "to": "b", "distance": 10.0},
            {"from": "a", "to": "end", "distance": 5.0},
            {"from": "b", "to": "end", "distance": 5.0},
        ],
    )
    rt = build_graph_runtime(path)
    result = bidirectional_dijkstra(rt.adjacency, "hub", "end")
    assert result.node_ids == ["hub", "a", "end"]
    assert result.graph_distance_meters == pytest.approx(15.0)


def test_tie_break_is_deterministic_across_repeated_runs(tmp_path):
    path = _write_graph(
        tmp_path,
        nodes={
            "s": {"latitude": 0.0, "longitude": 0.0},
            "x": {"latitude": 0.1, "longitude": 0.0},
            "y": {"latitude": 0.2, "longitude": 0.0},
            "t": {"latitude": 1.0, "longitude": 0.0},
        },
        edges=[
            {"from": "s", "to": "x", "distance": 10.0},
            {"from": "s", "to": "y", "distance": 10.0},
            {"from": "x", "to": "t", "distance": 1.0},
            {"from": "y", "to": "t", "distance": 1.0},
        ],
    )
    rt = build_graph_runtime(path)
    first = bidirectional_dijkstra(rt.adjacency, "s", "t")
    for _ in range(20):
        again = bidirectional_dijkstra(rt.adjacency, "s", "t")
        assert again.node_ids == first.node_ids
        assert again.graph_distance_meters == pytest.approx(first.graph_distance_meters)


def test_prefers_shorter_competing_route(tmp_path):
    path = _write_graph(
        tmp_path,
        nodes={
            "s": {"latitude": 0.0, "longitude": 0.0},
            "fast": {"latitude": 0.5, "longitude": 0.0},
            "slow": {"latitude": 0.5, "longitude": 0.5},
            "t": {"latitude": 1.0, "longitude": 0.0},
        },
        edges=[
            {"from": "s", "to": "fast", "distance": 1.0},
            {"from": "fast", "to": "t", "distance": 1.0},
            {"from": "s", "to": "slow", "distance": 50.0},
            {"from": "slow", "to": "t", "distance": 50.0},
        ],
    )
    rt = build_graph_runtime(path)
    result = bidirectional_dijkstra(rt.adjacency, "s", "t")
    assert result.node_ids == ["s", "fast", "t"]
    assert result.graph_distance_meters == pytest.approx(2.0)


def test_no_route_error_detail_for_api_mapping():
    err = NoRouteError()
    assert str(err) == "No route found between selected points"
