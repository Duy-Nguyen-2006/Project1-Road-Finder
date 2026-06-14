import json
import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain.graph import build_directed_adjacency
from app.infrastructure.graph_loader import GraphValidationError, load_graph_data
from app.infrastructure.grid_index import GridSpatialIndex
from app.utils.distance import haversine_meters

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


def _brute_force_nearest(
    latitude: float,
    longitude: float,
    nodes: dict[str, tuple[float, float]],
) -> str:
    best_id = ""
    best_dist = math.inf
    for node_id, (lat, lon) in nodes.items():
        d = haversine_meters(latitude, longitude, lat, lon)
        if d < best_dist:
            best_dist = d
            best_id = node_id
    return best_id


def test_build_runtime_from_fixture_graph():
    from app.application.graph_runtime import build_graph_runtime

    runtime = build_graph_runtime(FIXTURE_GRAPH_PATH)
    assert runtime.metadata.graph_version == "hcm-fixture-v2"
    assert len(runtime.nodes) == 6
    assert len(runtime.metadata.graph_version) > 0
    assert runtime.route_cache.limit == 1000
    assert runtime.route_cache.size == 0


def test_adjacency_respects_directed_edges_and_cost_multipliers():
    graph = load_graph_data(FIXTURE_GRAPH_PATH)
    adj = build_directed_adjacency(graph)

    # node-start -> node-mid: distance=120.5, road_type=residential, multiplier=1.2 -> 144.6
    assert ("node-mid", 144.6) in adj["node-start"]
    assert ("node-start", 144.6) in adj["node-mid"]
    # node-mid -> node-end: distance=180.0, road_type=secondary, multiplier=1.0 -> 180.0
    assert ("node-end", 180.0) in adj["node-mid"]
    assert ("node-mid", 180.0) in adj["node-end"]
    # node-start -> node-north is oneway (no reverse)
    assert any(nid == "node-north" for nid, _ in adj["node-start"])
    assert not any(nid == "node-start" for nid, _ in adj.get("node-north", []))


def test_grid_index_matches_brute_force_on_fixture_points():
    graph = load_graph_data(FIXTURE_GRAPH_PATH)
    node_coords = {
        nid: (n.latitude, n.longitude) for nid, n in graph.nodes.items()
    }
    grid = GridSpatialIndex(graph.nodes, graph.metadata.bbox)

    probe_points = [
        (10.778109, 106.714456),
        (10.7792, 106.7155),
        (10.7805, 106.7168),
        (10.7785, 106.7150),
        (10.7799, 106.7160),
    ]
    for lat, lon in probe_points:
        grid_id = grid.nearest_node_id(lat, lon)
        brute_id = _brute_force_nearest(lat, lon, node_coords)
        assert grid_id == brute_id


def test_build_runtime_fails_for_missing_graph(tmp_path):
    from app.application.graph_runtime import build_graph_runtime

    missing = tmp_path / "missing.json"
    with pytest.raises(GraphValidationError, match="not found"):
        build_graph_runtime(missing)


def test_build_runtime_fails_for_malformed_graph(tmp_path):
    from app.application.graph_runtime import build_graph_runtime

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(GraphValidationError, match="malformed"):
        build_graph_runtime(bad)


def test_app_startup_fails_when_graph_missing(monkeypatch, tmp_path):
    missing = tmp_path / "nograph.json"
    monkeypatch.setenv("ROAD_FINDER_GRAPH_PATH", str(missing))

    from app.main import create_app

    with pytest.raises(GraphValidationError):
        with TestClient(create_app()) as _client:
            pass


def test_app_startup_loads_graph_when_valid(monkeypatch):
    monkeypatch.setenv("ROAD_FINDER_GRAPH_PATH", str(FIXTURE_GRAPH_PATH))

    from app.main import create_app

    with TestClient(create_app()) as client:
        assert client.app.state.graph_runtime is not None
        assert client.app.state.graph_runtime.metadata.graph_version == "hcm-fixture-v2"


def test_graph_loads_during_lifespan_not_lazy_on_first_request(monkeypatch):
    monkeypatch.setenv("ROAD_FINDER_GRAPH_PATH", str(FIXTURE_GRAPH_PATH))

    from app.main import create_app

    with TestClient(create_app()) as client:
        runtime = client.app.state.graph_runtime
        assert runtime is not None
        assert len(runtime.adjacency) >= 4
