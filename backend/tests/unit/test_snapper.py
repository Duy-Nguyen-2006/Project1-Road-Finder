import json
import math
from pathlib import Path

import pytest

from app.application.graph_runtime import build_graph_runtime
from app.domain.errors import AcceptedAreaError
from app.domain.snapper import snap_point
from app.utils.distance import haversine_meters

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


@pytest.fixture
def runtime():
    return build_graph_runtime(FIXTURE_GRAPH_PATH)


def _write_snap_test_graph(tmp_path: Path, nodes: dict, max_snap: float = 200.0) -> Path:
    path = tmp_path / "snap_graph.json"
    payload = {
        "metadata": {
            "graph_version": "snap-test-v1",
            "bbox": {
                "min_latitude": 10.0,
                "min_longitude": 106.0,
                "max_latitude": 11.0,
                "max_longitude": 107.0,
            },
            "max_snap_distance_meters": max_snap,
        },
        "nodes": nodes,
        "edges": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_rejects_latitude_below_bbox_min(runtime):
    with pytest.raises(AcceptedAreaError):
        snap_point(runtime, 10.699999, 106.75)


def test_rejects_longitude_above_bbox_max(runtime):
    with pytest.raises(AcceptedAreaError):
        snap_point(runtime, 10.8, 106.900001)


def test_accepts_point_on_bbox_min_corners(tmp_path):
    """VAL-DOM-025: min latitude/longitude boundaries are inclusive (not outside-bbox)."""
    path = _write_snap_test_graph(
        tmp_path,
        {"corner": {"latitude": 10.0, "longitude": 106.0}},
    )
    rt = build_graph_runtime(path)
    result = snap_point(rt, 10.0, 106.0)
    assert result.node_id == "corner"
    assert result.distance_meters == pytest.approx(0.0, abs=1e-6)


def test_accepts_point_on_bbox_max_corners(tmp_path):
    path = _write_snap_test_graph(
        tmp_path,
        {"corner": {"latitude": 11.0, "longitude": 107.0}},
    )
    rt = build_graph_runtime(path)
    result = snap_point(rt, 11.0, 107.0)
    assert result.node_id == "corner"


def test_rejects_inside_bbox_beyond_max_snap_distance(runtime):
    with pytest.raises(AcceptedAreaError):
        snap_point(runtime, 10.85, 106.85)


def test_snaps_to_expected_node_at_clicked_coordinate(runtime):
    result = snap_point(runtime, 10.778109, 106.714456)
    assert result.node_id == "node-start"
    assert result.distance_meters == pytest.approx(0.0, abs=1e-6)


def test_snap_distance_is_haversine_to_snapped_node(runtime):
    lat, lon = 10.7790, 106.7150
    result = snap_point(runtime, lat, lon)
    node = runtime.nodes[result.node_id]
    expected = haversine_meters(lat, lon, node.latitude, node.longitude)
    assert result.distance_meters == pytest.approx(expected, rel=1e-9)


def test_snapping_is_deterministic_across_repeated_calls(runtime):
    lat, lon = 10.7792, 106.7155
    first = snap_point(runtime, lat, lon)
    for _ in range(5):
        again = snap_point(runtime, lat, lon)
        assert again.node_id == first.node_id
        assert again.distance_meters == pytest.approx(first.distance_meters)


def test_rejects_distance_just_over_max_snap_threshold(tmp_path):
    anchor_lat, anchor_lon = 10.5, 106.5
    path = _write_snap_test_graph(
        tmp_path,
        {"only": {"latitude": anchor_lat, "longitude": anchor_lon}},
        max_snap=200.0,
    )
    rt = build_graph_runtime(path)
    max_m = rt.metadata.max_snap_distance_meters
    lat = anchor_lat + (max_m + 1.0) / 111_320.0
    dist = haversine_meters(anchor_lat, anchor_lon, lat, anchor_lon)
    assert dist > max_m
    with pytest.raises(AcceptedAreaError):
        snap_point(rt, lat, anchor_lon)


def test_accepts_distance_exactly_at_max_snap_threshold(tmp_path):
    anchor_lat, anchor_lon = 10.5, 106.5
    path = _write_snap_test_graph(
        tmp_path,
        {"only": {"latitude": anchor_lat, "longitude": anchor_lon}},
        max_snap=200.0,
    )
    rt = build_graph_runtime(path)
    max_m = rt.metadata.max_snap_distance_meters
    lo, hi = 0.0, max_m / 90_000.0
    for _ in range(48):
        mid = (lo + hi) / 2
        lat = anchor_lat + mid
        d = haversine_meters(anchor_lat, anchor_lon, lat, anchor_lon)
        if d < max_m:
            lo = mid
        else:
            hi = mid
    lat = anchor_lat + lo
    dist = haversine_meters(anchor_lat, anchor_lon, lat, anchor_lon)
    assert dist <= max_m + 0.05
    assert math.isclose(dist, max_m, rel_tol=0, abs_tol=0.05)
    result = snap_point(rt, lat, anchor_lon)
    assert result.node_id == "only"
    assert result.distance_meters == pytest.approx(dist, rel=1e-6, abs=0.05)


def test_accepted_area_error_detail_for_api_mapping():
    err = AcceptedAreaError()
    assert str(err) == "Error: Not in accepted area"
