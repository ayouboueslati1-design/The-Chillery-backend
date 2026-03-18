from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    content: str

class ReviewCreate(ReviewBase):
    author_name: Optional[str] = None

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = None
    content: Optional[str] = None

class ReviewResponse(ReviewBase):
    id: UUID
    product_id: UUID
    user_id: Optional[UUID] = None
    author_name: Optional[str] = None
    verified_purchase: bool
    helpful_count: int
    is_approved: bool
    response: Optional[str] = None
    response_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReviewApprove(BaseModel):
    is_approved: bool
    response: Optional[str] = None
