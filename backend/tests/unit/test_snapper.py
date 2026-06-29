import json
from pathlib import Path

import pytest

from app.application.graph_runtime import build_graph_runtime
from app.domain.errors import AcceptedAreaError
from app.application.snap_service import snap_point
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


def test_accepts_point_far_inside_bbox(runtime):
    """Any point inside the bbox is accepted; the 200m snap limit was
    removed so the user can click anywhere in the supported area, even
    if no node is within 200m. The nearest node is still returned and
    the snap distance is reported on the leg."""
    result = snap_point(runtime, 10.85, 106.85)
    assert result.node_id  # some node was returned
    assert result.distance_meters > 0.0


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


def test_accepted_area_error_detail_for_api_mapping():
    err = AcceptedAreaError()
    assert str(err) == "Error: Not in accepted area"
