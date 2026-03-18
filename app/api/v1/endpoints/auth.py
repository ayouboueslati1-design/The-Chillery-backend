from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, LoginRequest
from app.services.auth import AuthService
from app.api import deps

router = APIRouter()


def _cookie_policy(request: Request) -> tuple[bool, str]:
    """
    Choose cookie policy for same-site vs cross-site requests.

    - Same-site (localhost frontend -> localhost backend): Lax + non-secure in dev
    - Cross-site (e.g. ngrok frontend -> localhost backend): None + Secure
    """
    origin = request.headers.get("origin")
    backend_host = request.url.hostname or ""

    is_cross_site = False
    if origin:
        try:
            origin_host = (urlparse(origin).hostname or "").lower()
            is_cross_site = bool(origin_host and backend_host and origin_host != backend_host)
        except Exception:
            is_cross_site = False

    if is_cross_site:
        return True, "none"

    is_secure = settings.ENVIRONMENT == "production"
    return is_secure, "lax"


def _set_auth_cookies(response: Response, tokens: dict, request: Request) -> None:
    """Write access and refresh tokens as HttpOnly cookies."""
    is_secure, same_site = _cookie_policy(request)
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=is_secure,
        samesite=same_site,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        secure=is_secure,
        samesite=same_site,
        path="/api/v1/auth/refresh",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(
    request: Request,
    response: Response,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new client user."""
    service = AuthService(db)
    user = await service.register_user(user_data)
    tokens = await service.create_tokens(user)
    _set_auth_cookies(response, tokens, request)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password; sets HttpOnly cookies and returns tokens."""
    service = AuthService(db)
    user = await service.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tokens = await service.create_tokens(user)
    _set_auth_cookies(response, tokens, request)
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token_body: Optional[str] = Body(None, embed=True, alias="refresh_token"),
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and issue a new access token."""
    # Browser clients send the cookie automatically; API clients pass the body field.
    token = request.cookies.get("refresh_token") or refresh_token_body
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    service = AuthService(db)
    tokens = await service.rotate_refresh_token(token)
    _set_auth_cookies(response, tokens, request)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response):
    """Clear auth cookies."""
    is_secure, same_site = _cookie_policy(request)
    response.delete_cookie(
        "access_token", path="/", secure=is_secure, httponly=True, samesite=same_site
    )
    response.delete_cookie(
        "refresh_token",
        path="/api/v1/auth/refresh",
        secure=is_secure,
        httponly=True,
        samesite=same_site,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(deps.get_current_user)):
    """Get current authenticated user info."""
    return current_user