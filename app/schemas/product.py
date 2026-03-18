from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from .product_image import ProductImageResponse
from .category import CategoryResponse

class ProductBase(BaseModel):
    sku: Optional[str] = None
    name: str
    description: str
    price: float
    compare_at_price: Optional[float] = None
    cost: Optional[float] = None
    low_stock_threshold: int = 5
    features: List[str] = []
    colors: List[str] = []
    sizes: List[str] = []
    tags: List[str] = []
    arrival_date: Optional[datetime] = None
    weight: Optional[float] = None
    dimensions: Optional[dict] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    category_id: Optional[UUID] = None
    stock_quantity: int = 0
    image_urls: List[str] = []  # Relative paths like /uploads/uuid.jpg

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    compare_at_price: Optional[float] = None
    cost: Optional[float] = None
    category_id: Optional[UUID] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    features: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    arrival_date: Optional[datetime] = None
    weight: Optional[float] = None
    dimensions: Optional[dict] = None
    is_active: Optional[bool] = None
    image_urls: Optional[List[str]] = None  # None = don't touch images; [] = remove all

class ProductListResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    price: float
    compare_at_price: Optional[float] = None
    category_id: Optional[UUID] = None
    in_stock: bool
    is_new: bool
    stock_quantity: int = 0
    low_stock_threshold: int = 5
    images: List[ProductImageResponse] = []
    tags: List[str] = []
    reviews_count: Optional[int] = 0
    average_rating: Optional[float] = 0.0
    
    model_config = ConfigDict(from_attributes=True)

class ProductResponse(ProductListResponse):
    sku: Optional[str]
    description: str
    stock_quantity: int
    low_stock_threshold: int
    features: List[str]
    colors: List[str]
    sizes: List[str]
    arrival_date: Optional[datetime]
    weight: Optional[float]
    dimensions: Optional[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)
