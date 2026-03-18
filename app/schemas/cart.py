from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.product import ProductListResponse


class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = 1
    selected_color: Optional[str] = None
    selected_size: Optional[str] = None


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: str
    product_id: str
    quantity: int
    selected_color: Optional[str] = None
    selected_size: Optional[str] = None
    product: ProductListResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total: float
    count: int
