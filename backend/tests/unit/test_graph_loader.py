import json
from pathlib import Path

import pytest

from app.infrastructure.graph_loader import (
    GraphValidationError,
    load_graph_data,
    validate_graph_data,
)

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


def _write_graph(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_loads_spec_shaped_fixture_graph():
    graph = load_graph_data(FIXTURE_GRAPH_PATH)
    assert graph.metadata.graph_version == "hcm-fixture-v1"
    assert graph.metadata.max_snap_distance_meters == 200
    assert len(graph.nodes) == 4
    assert len(graph.edges) == 2


def test_rejects_missing_metadata(tmp_path):
    path = _write_graph(
        tmp_path,
        {"nodes": {"a": {"latitude": 10.8, "longitude": 106.7}}, "edges": []},
    )
    with pytest.raises(GraphValidationError, match="metadata"):
        load_graph_data(path)


def test_rejects_empty_graph_version(tmp_path):
    path = _write_graph(
        tmp_path,
        {
            "metadata": {
                "graph_version": "",
                "bbox": {
                    "min_latitude": 10.7,
                    "min_longitude": 106.6,
                    "max_latitude": 10.9,
                    "max_longitude": 106.9,
                },
                "max_snap_distance_meters": 200,
            },
            "nodes": {"a": {"latitude": 10.8, "longitude": 106.7}},
            "edges": [],
        },
    )
    with pytest.raises(GraphValidationError, match="graph_version"):
        load_graph_data(path)


def test_rejects_inverted_bbox(tmp_path):
    path = _write_graph(
        tmp_path,
        {
            "metadata": {
                "graph_version": "v1",
                "bbox": {
                    "min_latitude": 10.9,
                    "min_longitude": 106.6,
                    "max_latitude": 10.7,
                    "max_longitude": 106.9,
                },
                "max_snap_distance_meters": 200,
            },
            "nodes": {"a": {"latitude": 10.8, "longitude": 106.7}},
            "edges": [],
        },
    )
    with pytest.raises(GraphValidationError, match="bbox"):
        load_graph_data(path)


def test_rejects_non_positive_max_snap_distance(tmp_path):
    path = _write_graph(
        tmp_path,
        {
            "metadata": {
                "graph_version": "v1",
                "bbox": {
                    "min_latitude": 10.7,
                    "min_longitude": 106.6,
                    "max_latitude": 10.9,
                    "max_longitude": 106.9,
                },
                "max_snap_distance_meters": 0,
            },
            "nodes": {"a": {"latitude": 10.8, "longitude": 106.7}},
            "edges": [],
        },
    )
    with pytest.raises(GraphValidationError, match="max_snap_distance"):
        load_graph_data(path)


def test_rejects_invalid_latitude(tmp_path):
    path = _write_graph(
        tmp_path,
        {
            "metadata": {
                "graph_version": "v1",
                "bbox": {
                    "min_latitude": 10.7,
                    "min_longitude": 106.6,
                    "max_latitude": 10.9,
                    "max_longitude": 106.9,
                },
                "max_snap_distance_meters": 200,
            },
            "nodes": {"a": {"latitude": 95.0, "longitude": 106.7}},
            "edges": [],
        },
    )
    with pytest.raises(GraphValidationError, match="latitude"):
        load_graph_data(path)


def test_rejects_node_outside_bbox(tmp_path):
    path = _write_graph(
        tmp_path,
        {
            "metadata": {
                "graph_version": "v1",
                "bbox": {
                    "min_latitude": 10.7,
                    "min_longitude": 106.6,
                    "max_latitude": 10.9,
                    "max_longitude": 106.9,
                },
                "max_snap_distance_meters": 200,
            },
            "nodes": {"a": {"latitude": 10.5, "longitude": 106.7}},
            "edges": [],
        },
    )
    with pytest.raises(GraphValidationError, match="bbox"):
        load_graph_data(path)


def test_rejects_edge_referencing_missing_node(tmp_path):
    path = _write_graph(
        tmp_path,
        {
            "metadata": {
                "graph_version": "v1",
                "bbox": {
                    "min_latitude": 10.7,
                    "min_longitude": 106.6,
                    "max_latitude": 10.9,
                    "max_longitude": 106.9,
                },
                "max_snap_distance_meters": 200,
            },
            "nodes": {"a": {"latitude": 10.8, "longitude": 106.7}},
            "edges": [{"from": "a", "to": "missing", "distance": 10.0}],
        },
    )
    with pytest.raises(GraphValidationError, match="node"):
        load_graph_data(path)


def test_rejects_non_positive_edge_distance(tmp_path):
    path = _write_graph(
        tmp_path,
        {
            "metadata": {
                "graph_version": "v1",
                "bbox": {
                    "min_latitude": 10.7,
                    "min_longitude": 106.6,
                    "max_latitude": 10.9,
                    "max_longitude": 106.9,
                },
                "max_snap_distance_meters": 200,
            },
            "nodes": {
                "a": {"latitude": 10.8, "longitude": 106.7},
                "b": {"latitude": 10.81, "longitude": 106.71},
            },
            "edges": [{"from": "a", "to": "b", "distance": 0}],
        },
    )
    with pytest.raises(GraphValidationError, match="distance"):
        load_graph_data(path)


def test_development_graph_artifact_is_spec_shaped_and_under_size_cap():
    assert FIXTURE_GRAPH_PATH.exists()
    size_bytes = FIXTURE_GRAPH_PATH.stat().st_size
    assert size_bytes < 50 * 1024 * 1024
    raw = json.loads(FIXTURE_GRAPH_PATH.read_text(encoding="utf-8"))
    graph = validate_graph_data(raw)
    assert graph.metadata.graph_version
    assert graph.nodes
    assert graph.edges


def test_backend_runtime_does_not_import_generator_packages():
    graph_loader_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "infrastructure"
        / "graph_loader.py"
    )
    source = graph_loader_path.read_text(encoding="utf-8")
    assert "osmnx" not in source
    assert "networkx" not in source
