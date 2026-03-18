from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.config import settings
from app.models.user import User, UserRole

# auto_error=False so a missing/invalid token never raises 401 inside this scheme;
# the dependency functions below handle the 401 themselves.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _extract_token(request: Request, bearer_token: Optional[str]) -> Optional[str]:
    """Read JWT from HttpOnly cookie first, then fall back to Authorization header."""
    cookie = request.cookies.get("access_token")
    if cookie:
        return cookie
    return bearer_token  # may be None if no header was provided


async def get_current_user(
    request: Request,
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = _extract_token(request, bearer_token)
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


# Role-based access control
def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' required",
            )
        return current_user

    return role_checker


# Convenience dependencies
get_current_client = require_role(UserRole.CLIENT)
get_current_admin = require_role(UserRole.ADMIN)
get_current_super_admin = require_role(UserRole.SUPER_ADMIN)


async def get_optional_current_user(
    request: Request,
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Returns the authenticated User, or None for unauthenticated requests."""
    token = _extract_token(request, bearer_token)
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            return None
    except JWTError:
        return None

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    return result.scalar_one_or_none()