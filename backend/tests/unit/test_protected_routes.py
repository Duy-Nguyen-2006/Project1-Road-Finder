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
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("post", "/route", {"start": VALID_START, "end": VALID_END}),
        (
            "post",
            "/assignments",
            {
                "order": {
                    "id": "o1",
                    "pickup": VALID_START,
                    "dropoff": VALID_END,
                },
                "shippers": [
                    {"id": "s1", "location": VALID_START},
                ],
            },
        ),
        (
            "post",
            "/tours",
            {
                "shipper": {"id": "s1", "location": VALID_START},
                "orders": [
                    {
                        "id": "o1",
                        "pickup": VALID_START,
                        "dropoff": VALID_END,
                    }
                ],
            },
        ),
        (
            "post",
            "/fleet",
            {
                "shippers": [{"id": "s1", "location": VALID_START}],
                "orders": [
                    {
                        "id": "o1",
                        "pickup": VALID_START,
                        "dropoff": VALID_END,
                    }
                ],
            },
        ),
    ],
)
def test_compute_endpoints_require_auth(client, method, path, payload):
    response = getattr(client, method)(path, json=payload)
    assert response.status_code == 401


def test_health_and_bounds_remain_public(client):
    assert client.get("/health").status_code == 200
    assert client.get("/graph/bounds").status_code == 200