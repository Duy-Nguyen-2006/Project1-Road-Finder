from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException

from app.auth.supabase_jwt import verify_access_token
from app.domain.errors import AuthError


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    return token or None


def optional_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict | None:
    """Return JWT claims when a valid Bearer token is present; else None."""
    token = _extract_bearer(authorization)
    if token is None:
        return None
    try:
        return verify_access_token(token)
    except AuthError:
        return None


def require_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """Require a valid Supabase JWT; raise 401 otherwise."""
    token = _extract_bearer(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="Thiếu token đăng nhập")
    try:
        return verify_access_token(token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc