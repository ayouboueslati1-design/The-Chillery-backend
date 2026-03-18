from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    guest_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    guest_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[OrderStatus] = mapped_column(String(32), default=OrderStatus.PENDING)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        String(32), default=PaymentStatus.UNPAID
    )

    transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    auth_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount_total: Mapped[float] = mapped_column(Float, nullable=False)

    shipping_address: Mapped[dict] = mapped_column(JSON, default=dict)
    shipping_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    user: Mapped["User"] = relationship("User", back_populates="orders")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[str | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )

    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product")
