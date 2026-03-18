from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
from app.api import deps
from app.db.session import get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services.product import ProductService
from app.services.review import ReviewService

router = APIRouter()

@router.get("/", response_model=dict) # Using dict to include metadata (count)
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category_slug: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = Query("newest", description="price_asc, price_desc, name_asc, name_desc, newest"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve products with filtering, pagination, and sorting."""
    service = ProductService(db)
    products, total = await service.get_products(
        skip=skip, limit=limit, category_slug=category_slug,
        min_price=min_price, max_price=max_price, in_stock=in_stock,
        search=search, sort_by=sort_by
    )
    
    # Normally we'd serialize this properly with a custom response model, but this works for dict response
    results = [ProductListResponse.model_validate(p) for p in products]
    
    return {
        "items": results,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{slug}", response_model=ProductResponse)
async def get_product(
    slug: str, db: AsyncSession = Depends(get_db)
):
    """Retrieve product details by slug."""
    service = ProductService(db)
    prod = await service.get_product_by_slug(slug)
    count, avg = await service.get_review_stats(prod.id)
    prod.reviews_count = count
    prod.average_rating = avg
    return prod


@router.get("/id/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: str, db: AsyncSession = Depends(get_db)
):
    """Retrieve product details by exact ID."""
    service = ProductService(db)
    prod = await service.get_product_by_id(product_id)
    count, avg = await service.get_review_stats(prod.id)
    prod.reviews_count = count
    prod.average_rating = avg
    return prod

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_admin)
):
    """Create a new product. Admin only."""
    service = ProductService(db)
    prod = await service.create_product(data)
    prod.reviews_count = 0 
    prod.average_rating = 0.0
    return prod

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(deps.get_current_admin),
):
    """Update a product. Admin only."""
    service = ProductService(db)
    prod = await service.update_product(product_id, data)
    count, avg = await service.get_review_stats(prod.id)
    prod.reviews_count = count
    prod.average_rating = avg
    return prod

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_admin)
):
    """Delete a product (soft delete). Admin only."""
    service = ProductService(db)
    await service.delete_product(product_id)

@router.get("/{slug}/reviews", response_model=list[ReviewResponse])
async def get_product_reviews(
    slug: str,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List approved reviews for a product."""
    product_service = ProductService(db)
    try:
        uuid_obj = uuid.UUID(slug, version=4)
        prod = await product_service.get_product_by_id(str(uuid_obj))
    except ValueError:
        prod = await product_service.get_product_by_slug(slug)

    review_service = ReviewService(db)
    return await review_service.get_reviews_for_product(
        product_id=str(prod.id), skip=skip, limit=limit
    )


@router.post("/{slug}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_product_review(
    slug: str,
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(deps.get_optional_current_user),
):
    """Create a review for a product."""
    product_service = ProductService(db)
    try:
        uuid_obj = uuid.UUID(slug, version=4)
        prod = await product_service.get_product_by_id(str(uuid_obj))
    except ValueError:
        prod = await product_service.get_product_by_slug(slug)

    review_service = ReviewService(db)
    user_id_str = str(current_user.id) if current_user else None
    return await review_service.create_review(
        product_id=str(prod.id), data=data, user_id=user_id_str
    )
