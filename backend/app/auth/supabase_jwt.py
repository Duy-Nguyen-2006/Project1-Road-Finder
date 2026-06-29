from __future__ import annotations

import os
from functools import lru_cache

import jwt
from jwt import PyJWKClient, PyJWKClientError

from app.domain.errors import AuthError


def _supabase_url() -> str:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if not url:
        raise AuthError("SUPABASE_URL is not configured")
    return url


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(f"{_supabase_url()}/auth/v1/.well-known/jwks.json")


def _decode_hs256(token: str) -> dict:
    secret = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
    if not secret:
        raise AuthError("SUPABASE_JWT_SECRET is not configured for HS256 tokens")
    return jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience="authenticated",
        issuer=f"{_supabase_url()}/auth/v1",
    )


def _decode_asymmetric(token: str) -> dict:
    signing_key = _jwks_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        issuer=f"{_supabase_url()}/auth/v1",
    )


def verify_access_token(token: str) -> dict:
    """Verify a Supabase-issued JWT and return its claims."""
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") == "HS256":
            return _decode_hs256(token)
        return _decode_asymmetric(token)
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token đã hết hạn") from exc
    except AuthError:
        raise
    except (jwt.InvalidTokenError, PyJWKClientError) as exc:
        raise AuthError("Token không hợp lệ") from exc
    except Exception as exc:
        raise AuthError("Không xác thực được token") from exc