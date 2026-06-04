from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.services.shortest_path_service import find_cached_or_compute_graph_path

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)


def test_health_observes_cache_growth_and_stable_repeat(monkeypatch):
    monkeypatch.setenv("ROAD_FINDER_GRAPH_PATH", str(FIXTURE_GRAPH_PATH))
    from app.main import create_app

    with TestClient(create_app()) as client:
        before = client.get("/health").json()
        assert before["cache"]["route_cache_size"] == 0
        assert before["cache"]["route_cache_limit"] == 1000

        runtime = client.app.state.graph_runtime
        find_cached_or_compute_graph_path(
            runtime, (10.7785, 106.7149), (10.7808, 106.7172)
        )
        after_first = client.get("/health").json()
        assert after_first["cache"]["route_cache_size"] == 1

        find_cached_or_compute_graph_path(
            runtime, (10.7786, 106.7150), (10.7808, 106.7172)
        )
        after_repeat = client.get("/health").json()
        assert after_repeat["cache"]["route_cache_size"] == 1

        find_cached_or_compute_graph_path(
            runtime, (10.7808, 106.7172), (10.7785, 106.7149)
        )
        after_reverse = client.get("/health").json()
        assert after_reverse["cache"]["route_cache_size"] == 1
        assert after_reverse["cache"]["route_cache_limit"] == 1000
