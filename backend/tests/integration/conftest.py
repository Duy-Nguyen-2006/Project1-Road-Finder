from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain.errors import AuthError

FIXTURE_GRAPH_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "data" / "road_graph.json"
)

TEST_AUTH_HEADER = {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def mock_jwt(monkeypatch):
    def fake_verify(token: str) -> dict:
        if token == "test-token":
            return {
                "sub": "00000000-0000-0000-0000-000000000001",
                "email": "test@example.com",
                "role": "authenticated",
            }
        raise AuthError("Token không hợp lệ")

    monkeypatch.setattr("app.auth.dependencies.verify_access_token", fake_verify)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ROAD_FINDER_GRAPH_PATH", str(FIXTURE_GRAPH_PATH))
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        original_request = test_client.request

        def authed_request(method, url, **kwargs):
            headers = dict(kwargs.pop("headers", None) or {})
            if "Authorization" not in headers:
                headers.update(TEST_AUTH_HEADER)
            kwargs["headers"] = headers
            return original_request(method, url, **kwargs)

        test_client.request = authed_request
        yield test_client