import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    return TestClient(create_app())


def test_auth_session_unauthenticated(client):
    response = client.get("/auth/session")
    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


def test_auth_me_requires_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401