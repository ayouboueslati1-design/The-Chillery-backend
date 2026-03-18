from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_active: bool = True
    sort_order: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class CategoryResponse(CategoryBase):
    id: UUID
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CategoryTreeResponse(CategoryResponse):
    children: list["CategoryTreeResponse"] = []
