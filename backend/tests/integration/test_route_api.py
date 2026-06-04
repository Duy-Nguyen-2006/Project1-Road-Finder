from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)

VALID_START = {"latitude": 10.7785, "longitude": 106.7149}
VALID_END = {"latitude": 10.7808, "longitude": 106.7172}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ROAD_FINDER_GRAPH_PATH", str(FIXTURE_GRAPH_PATH))
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c


def test_graph_bounds_returns_metadata(client):
    response = client.get("/graph-bounds")
    assert response.status_code == 200
    body = response.json()
    assert body["graph_version"] == "hcm-fixture-v1"
    assert body["max_snap_distance_meters"] == 200
    bbox = body["bbox"]
    assert bbox["min_latitude"] == pytest.approx(10.7)
    assert bbox["min_longitude"] == pytest.approx(106.6)
    assert bbox["max_latitude"] == pytest.approx(10.9)
    assert bbox["max_longitude"] == pytest.approx(106.9)


def test_shortest_path_happy_path(client):
    response = client.post(
        "/shortest-path",
        json={"start": VALID_START, "end": VALID_END},
    )
    assert response.status_code == 200
    body = response.json()
    assert "ordered_points" not in body
    assert body["start_node_id"]
    assert body["end_node_id"]
    assert body["distance"] > 0
    assert len(body["route_points"]) >= 2
    assert body["route_points"][0]["latitude"] == pytest.approx(
        VALID_START["latitude"]
    )
    assert body["route_points"][-1]["latitude"] == pytest.approx(
        VALID_END["latitude"]
    )


def test_shortest_path_invalid_latitude_returns_422(client):
    response = client.post(
        "/shortest-path",
        json={
            "start": {"latitude": 91.0, "longitude": 106.71},
            "end": VALID_END,
        },
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_shortest_path_outside_bbox_returns_exact_detail(client):
    response = client.post(
        "/shortest-path",
        json={
            "start": {"latitude": 10.69, "longitude": 106.75},
            "end": VALID_END,
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Error: Not in accepted area"


def test_shortest_path_disconnected_returns_404(client):
    response = client.post(
        "/shortest-path",
        json={
            "start": {"latitude": 10.7785, "longitude": 106.7149},
            "end": {"latitude": 10.75, "longitude": 106.65},
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No route found between selected points"


def test_shortest_path_is_deterministic(client):
    payload = {"start": VALID_START, "end": VALID_END}
    first = client.post("/shortest-path", json=payload).json()
    second = client.post("/shortest-path", json=payload).json()
    assert first["route_points"] == second["route_points"]
    assert first["distance"] == pytest.approx(second["distance"])
    assert first["start_node_id"] == second["start_node_id"]
    assert first["end_node_id"] == second["end_node_id"]


def test_optimize_route_two_points_matches_shortest_path(client):
    points = [VALID_START, VALID_END]
    sp = client.post(
        "/shortest-path", json={"start": points[0], "end": points[1]}
    ).json()
    opt = client.post("/optimize-route", json={"points": points}).json()
    assert "ordered_points" not in opt
    assert opt["route_points"] == sp["route_points"]
    assert opt["distance"] == pytest.approx(sp["distance"])
    assert opt["start_node_id"] == sp["start_node_id"]
    assert opt["end_node_id"] == sp["end_node_id"]


@pytest.mark.parametrize("point_count", [0, 1, 3])
def test_optimize_route_rejects_non_two_points(client, point_count):
    points = [VALID_START] * point_count if point_count else []
    response = client.post("/optimize-route", json={"points": points})
    assert response.status_code == 422
