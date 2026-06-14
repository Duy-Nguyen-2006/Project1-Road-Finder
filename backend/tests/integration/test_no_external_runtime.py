"""VAL-BE-015 / VAL-DOM-022: MVP route endpoints must not call external HTTP providers."""

from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)

VALID_START = {"latitude": 10.7785, "longitude": 106.7149}
VALID_END = {"latitude": 10.7808, "longitude": 106.7172}


class ExternalHttpBlocked(RuntimeError):
    """Raised when runtime code attempts Overpass/OSRM or other external HTTP."""


def _block_external_http(*_args, **_kwargs):
    raise ExternalHttpBlocked("external HTTP is blocked for MVP runtime tests")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ROAD_FINDER_GRAPH_PATH", str(FIXTURE_GRAPH_PATH))
    monkeypatch.setattr(requests, "get", _block_external_http)
    monkeypatch.setattr(requests, "post", _block_external_http)
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c


def test_health_graph_bounds_and_routes_without_external_http(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["graph"]["loaded"] is True

    bounds = client.get("/graph/bounds")
    assert bounds.status_code == 200
    assert bounds.json()["max_snap_distance_meters"] == 200

    route = client.post(
        "/route",
        json={"start": VALID_START, "end": VALID_END},
    )
    assert route.status_code == 200
    assert route.json()["distance"] > 0
    assert len(route.json()["route_points"]) >= 2
