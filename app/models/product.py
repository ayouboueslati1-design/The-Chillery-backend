from sqlalchemy import String, Boolean, ForeignKey, Integer, Numeric, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import uuid
from datetime import datetime, timedelta, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    compare_at_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5)
    
    features: Mapped[list[str]] = mapped_column(JSON, default=list)
    colors: Mapped[list[str]] = mapped_column(JSON, default=list)
    sizes: Mapped[list[str]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    arrival_date: Mapped[datetime | None] = mapped_column(nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimensions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage", 
        back_populates="product", 
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order"
    )
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def is_new(self) -> bool:
        if not self.arrival_date:
            return False
        # Consider new if arrived within last 30 days (compare naive datetimes)
        cutoff = _utcnow() - timedelta(days=30)
        return self.arrival_date >= cutoff
