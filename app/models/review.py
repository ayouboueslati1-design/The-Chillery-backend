from sqlalchemy import String, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import uuid
from datetime import datetime

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    response: Mapped[str | None] = mapped_column(String, nullable=True)
    response_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    user: Mapped["User"] = relationship("User")
