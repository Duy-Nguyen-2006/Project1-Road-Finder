from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.application.graph_runtime import build_graph_runtime
from app.application.health import build_health_payload

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


@pytest.fixture
def runtime():
    return build_graph_runtime(FIXTURE_GRAPH_PATH)


def test_build_health_payload_exposes_graph_and_cache(runtime):
    payload = build_health_payload(runtime)
    assert payload["status"] == "ok"
    assert payload["graph"]["loaded"] is True
    assert payload["graph"]["graph_version"] == "hcm-fixture-v2"
    assert payload["graph"]["node_count"] == 6
    assert payload["graph"]["edge_count"] == 5
    assert payload["cache"]["route_cache_limit"] == 1000
    assert payload["cache"]["route_cache_size"] == 0


def test_health_endpoint_returns_cache_metadata(monkeypatch):
    monkeypatch.setenv("ROAD_FINDER_GRAPH_PATH", str(FIXTURE_GRAPH_PATH))
    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["cache"]["route_cache_limit"] == 1000
        assert body["cache"]["route_cache_size"] >= 0
        assert body["graph"]["loaded"] is True
