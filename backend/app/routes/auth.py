from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.security import require_actor, require_roles
from app.store import store

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str
    mfa_code: str | None = None


class CreateUserRequest(BaseModel):
    email: str
    name: str
    role: str = "ANALYST"
    password: str


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class MfaVerifyRequest(BaseModel):
    code: str


@router.post("/login")
async def login(payload: LoginRequest):
    user = store.authenticate_user(payload.email, payload.password, payload.mfa_code)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    session = store.create_session(user)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "user": _public_user(user),
    }


@router.get("/me")
async def me(actor: dict = Depends(require_actor)):
    return {"user": _public_user(actor)}


@router.post("/users")
async def create_user(payload: CreateUserRequest, actor: dict = Depends(require_roles("ADMIN"))):
    if store.get_user_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    user = store.create_user(
        email=payload.email,
        name=payload.name,
        role=payload.role,
        password=payload.password,
    )
    return {"user": _public_user(user), "created_by": actor["email"]}


@router.post("/register")
async def register(payload: RegisterRequest):
    if not settings.allow_registration:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration is disabled")
    if store.get_user_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    user = store.create_user(
        email=payload.email,
        name=payload.name,
        role="ANALYST",
        password=payload.password,
    )
    session = store.create_session(user)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "user": _public_user(user),
    }


@router.post("/mfa/setup")
async def setup_mfa(actor: dict = Depends(require_actor)):
    details = store.prepare_mfa(actor["id"])
    if not details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return details


@router.post("/mfa/enable")
async def enable_mfa(payload: MfaVerifyRequest, actor: dict = Depends(require_actor)):
    if not store.enable_mfa(actor["id"], payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")
    return {"mfa_enabled": True}


@router.post("/mfa/disable")
async def disable_mfa(actor: dict = Depends(require_actor)):
    if not store.disable_mfa(actor["id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"mfa_enabled": False}


@router.get("/sso/config")
async def sso_config():
    return {
        "enabled": settings.oidc_enabled,
        "issuer": settings.oidc_issuer,
        "client_id": settings.oidc_client_id,
        "authorization_url": settings.oidc_authorization_url,
        "token_url": settings.oidc_token_url,
    }


def _public_user(user: dict) -> dict:
    return {key: value for key, value in user.items() if key not in {"mfa_secret"}}
