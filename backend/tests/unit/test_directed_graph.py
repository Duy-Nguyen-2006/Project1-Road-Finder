import json
from pathlib import Path

import pytest

from app.domain.cost_model import RoutingOptions
from app.domain.graph import build_directed_adjacency
from app.infrastructure.graph_loader import load_graph_data

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


def _write_graph(tmp_path: Path, nodes: dict, edges: list) -> Path:
    path = tmp_path / "graph.json"
    payload = {
        "metadata": {
            "graph_version": "directed-test-v1",
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


def test_oneway_edge_only_adds_forward_direction(tmp_path):
    path = _write_graph(
        tmp_path,
        nodes={
            "a": {"latitude": 1.0, "longitude": 1.0},
            "b": {"latitude": 2.0, "longitude": 2.0},
        },
        edges=[{"from": "a", "to": "b", "distance": 100.0, "oneway": True}],
    )
    graph = load_graph_data(path)
    adj = build_directed_adjacency(graph)

    # a -> b exists
    assert ("b", 100.0) in adj["a"]
    # b -> a does NOT exist (oneway)
    assert not any(nid == "a" for nid, _ in adj.get("b", []))


def test_bidirectional_edge_adds_both_directions(tmp_path):
    path = _write_graph(
        tmp_path,
        nodes={
            "a": {"latitude": 1.0, "longitude": 1.0},
            "b": {"latitude": 2.0, "longitude": 2.0},
        },
        edges=[{"from": "a", "to": "b", "distance": 100.0, "oneway": False}],
    )
    graph = load_graph_data(path)
    adj = build_directed_adjacency(graph)

    assert ("b", 100.0) in adj["a"]
    assert ("a", 100.0) in adj["b"]


def test_default_oneway_is_false(tmp_path):
    path = _write_graph(
        tmp_path,
        nodes={
            "a": {"latitude": 1.0, "longitude": 1.0},
            "b": {"latitude": 2.0, "longitude": 2.0},
        },
        edges=[{"from": "a", "to": "b", "distance": 100.0}],
    )
    graph = load_graph_data(path)
    adj = build_directed_adjacency(graph)

    # Default oneway=false -> both directions
    assert ("b", 100.0) in adj["a"]
    assert ("a", 100.0) in adj["b"]


def test_avoid_road_type_removes_edges(tmp_path):
    path = _write_graph(
        tmp_path,
        nodes={
            "a": {"latitude": 1.0, "longitude": 1.0},
            "b": {"latitude": 2.0, "longitude": 2.0},
        },
        edges=[
            {"from": "a", "to": "b", "distance": 100.0, "road_type": "residential"},
        ],
    )
    graph = load_graph_data(path)
    options = RoutingOptions(avoid_road_types=("residential",))
    adj = build_directed_adjacency(graph, options)

    # Residential edge is avoided -> no connection
    assert adj["a"] == []
    assert adj["b"] == []


def test_cost_model_applies_multiplier(tmp_path):
    path = _write_graph(
        tmp_path,
        nodes={
            "a": {"latitude": 1.0, "longitude": 1.0},
            "b": {"latitude": 2.0, "longitude": 2.0},
        },
        edges=[
            {"from": "a", "to": "b", "distance": 100.0, "road_type": "highway"},
        ],
    )
    graph = load_graph_data(path)
    adj = build_directed_adjacency(graph)

    # highway multiplier = 0.8, so 100 * 0.8 = 80
    assert ("b", 80.0) in adj["a"]


def test_fixture_has_oneway_edge():
    graph = load_graph_data(FIXTURE_GRAPH_PATH)
    adj = build_directed_adjacency(graph)

    # node-start -> node-north is oneway (forward only)
    assert any(nid == "node-north" for nid, _ in adj["node-start"])
    # node-north -> node-start should NOT exist (oneway)
    assert not any(nid == "node-start" for nid, _ in adj.get("node-north", []))


def test_fixture_has_mixed_road_types():
    graph = load_graph_data(FIXTURE_GRAPH_PATH)
    adj = build_directed_adjacency(graph)

    # node-start -> node-mid: residential (120.5 * 1.2 = 144.6)
    assert ("node-mid", 144.6) in adj["node-start"]
    # node-mid -> node-end: secondary (180.0 * 1.0 = 180.0)
    assert ("node-end", 180.0) in adj["node-mid"]
