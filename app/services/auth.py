from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.core.config import settings
from fastapi import HTTPException, status
from datetime import datetime, timezone
from jose import jwt, JWTError


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user_data: UserCreate) -> User:
        query = select(User).where(User.email == user_data.email)
        result = await self.db.execute(query)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        new_user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            date_of_birth=user_data.date_of_birth,
            role="client",
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        query = select(User).where(User.email == email, User.is_active == True)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def create_tokens(self, user: User) -> dict:
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        user.last_login = _utcnow()
        self.db.add(user)
        await self.db.commit()
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def rotate_refresh_token(self, refresh_token: str) -> dict:
        """Validate the incoming refresh token, then issue a new access+refresh pair."""
        try:
            payload = jwt.decode(
                refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
                )
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        query = select(User).where(User.id == user_id, User.is_active == True)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
            )

        # Issue a fresh pair (rotate the refresh token on every use)
        new_access = create_access_token(data={"sub": str(user.id)})
        new_refresh = create_refresh_token(data={"sub": str(user.id)})
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}
