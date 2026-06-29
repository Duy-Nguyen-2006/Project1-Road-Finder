from fastapi import APIRouter, Depends

from app.auth.dependencies import optional_current_user, require_current_user

router = APIRouter()


@router.get("/auth/me")
def auth_me(user: dict = Depends(require_current_user)) -> dict:
    return {
        "id": user.get("sub"),
        "email": user.get("email"),
        "role": user.get("role"),
    }


@router.get("/auth/session")
def auth_session(user: dict | None = Depends(optional_current_user)) -> dict:
    if user is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "id": user.get("sub"),
        "email": user.get("email"),
    }