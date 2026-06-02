from __future__ import annotations

from secrets import compare_digest

from fastapi import Header, HTTPException, status

from app.config import settings
from app.store import store


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.api_key:
        return
    if not x_api_key or not compare_digest(x_api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid X-API-Key header required",
        )


async def require_actor(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
) -> dict:
    if settings.api_key and x_api_key and compare_digest(x_api_key, settings.api_key):
        return {"id": "service", "email": "service@sentinelx.local", "name": "Service API", "role": "ADMIN"}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    token = authorization.split(" ", 1)[1].strip()
    user = store.get_user_for_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def require_roles(*roles: str):
    allowed = {role.upper() for role in roles}

    async def role_dependency(
        authorization: str | None = Header(default=None),
        x_api_key: str | None = Header(default=None),
    ) -> dict:
        actor = await require_actor(authorization=authorization, x_api_key=x_api_key)
        if actor.get("role", "").upper() not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return actor

    return role_dependency
