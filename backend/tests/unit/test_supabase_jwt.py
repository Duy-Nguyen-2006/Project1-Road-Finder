import time

import jwt
import pytest

from app.auth.supabase_jwt import verify_access_token
from app.domain.errors import AuthError


SUPABASE_URL = "https://example.supabase.co"
JWT_SECRET = "test-jwt-secret-for-hs256"


def _hs256_token(
    *,
    secret: str = JWT_SECRET,
    sub: str = "user-123",
    expired: bool = False,
) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": "authenticated",
        "iss": f"{SUPABASE_URL}/auth/v1",
        "exp": now - 10 if expired else now + 3600,
        "iat": now,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture(autouse=True)
def supabase_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", SUPABASE_URL)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)


def test_verify_hs256_token_success():
    token = _hs256_token()
    claims = verify_access_token(token)
    assert claims["sub"] == "user-123"
    assert claims["aud"] == "authenticated"


def test_verify_hs256_expired_token():
    token = _hs256_token(expired=True)
    with pytest.raises(AuthError, match="Token đã hết hạn"):
        verify_access_token(token)


def test_verify_hs256_invalid_signature():
    token = _hs256_token(secret="wrong-secret")
    with pytest.raises(AuthError, match="Token không hợp lệ"):
        verify_access_token(token)


def test_verify_hs256_missing_secret(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    token = _hs256_token()
    with pytest.raises(AuthError, match="SUPABASE_JWT_SECRET is not configured"):
        verify_access_token(token)


def test_verify_missing_supabase_url(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    token = _hs256_token()
    with pytest.raises(AuthError, match="SUPABASE_URL is not configured"):
        verify_access_token(token)