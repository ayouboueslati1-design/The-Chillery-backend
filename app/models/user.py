from sqlalchemy import String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum
import uuid
from datetime import datetime, timezone


def _utcnow() -> datetime:
    """Returns current UTC time as a timezone-naive datetime for DB columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

class UserRole(str, enum.Enum):
    CLIENT = "client"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str]= mapped_column(String(255), nullable= False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[datetime] = mapped_column(nullable=True)
    age_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CLIENT, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)
    last_login: Mapped[datetime] = mapped_column(nullable=True)

    #Relationships
    adresses: Mapped[list["Adress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    #reviews: Mapped[list["Review"]] = relationship(back_populates="user")
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    #wishlist_items: Mapped[list["WishlistItem"]] = relationship(back_populates="user")

class Adress(Base):
    __tablename__ ="adresses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    address_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'shipping' or 'billing'
    recipient_name: Mapped[str] = mapped_column(String(200), nullable=False)
    street_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    street_line2: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    #Relationships
    user: Mapped["User"] = relationship(back_populates="adresses")
