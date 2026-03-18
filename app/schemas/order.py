from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


OrderStatusLiteral = Literal[
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
    "refunded",
]

PaymentStatusLiteral = Literal["unpaid", "paid", "failed", "refunded"]


class ShippingAddress(BaseModel):
    full_name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)


class OrderCreateRequest(BaseModel):
    transaction_id: str
    auth_code: Optional[str] = None
    amount_total: float = Field(..., gt=0)
    items: list[OrderItemCreate]
    shipping_address: ShippingAddress
    shipping_method: Optional[str] = None
    guest_email: Optional[str] = None
    guest_name: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: Optional[str] = None
    product_name: str
    product_image: Optional[str] = None
    quantity: int
    unit_price: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: Optional[str] = None
    guest_email: Optional[str] = None
    guest_name: Optional[str] = None

    status: OrderStatusLiteral
    payment_status: PaymentStatusLiteral

    transaction_id: Optional[str] = None
    auth_code: Optional[str] = None
    amount_total: float

    shipping_address: dict
    shipping_method: Optional[str] = None
    tracking_number: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    skip: int
    limit: int


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatusLiteral
    tracking_number: Optional[str] = None
