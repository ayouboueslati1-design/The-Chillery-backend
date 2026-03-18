from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class ProductImageBase(BaseModel):
    url: str
    alt_text: Optional[str] = None
    sort_order: int = 0

class ProductImageCreate(ProductImageBase):
    product_id: UUID

class ProductImageResponse(ProductImageBase):
    id: UUID
    product_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
