from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from app.repositories.base import BaseRepository
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    
    async def get_by_id(self, db: AsyncSession, product_id: str) -> Optional[Product]:
        query = select(Product).options(
            selectinload(Product.images),
            selectinload(Product.category)
        ).where(Product.id == product_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Product]:
        query = select(Product).options(
            selectinload(Product.images),
            selectinload(Product.category)
        ).where(Product.slug == slug)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi_with_filters(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        category_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "newest"
    ) -> Tuple[List[Product], int]:
        
        # Base query for counting total
        base_query = select(Product).where(Product.is_active == True)
        
        # Apply filters
        if category_id:
            base_query = base_query.where(Product.category_id == category_id)
        if min_price is not None:
            base_query = base_query.where(Product.price >= min_price)
        if max_price is not None:
            base_query = base_query.where(Product.price <= max_price)
        if in_stock is not None:
            if in_stock:
                base_query = base_query.where(Product.stock_quantity > 0)
            else:
                base_query = base_query.where(Product.stock_quantity <= 0)
        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
            base_query = base_query.where(search_filter)

        # Count total matches before pagination
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar_one()

        # Build fetch query with relationships
        fetch_query = base_query.options(
            selectinload(Product.images),
            selectinload(Product.category)
        )

        # Apply sorting
        if sort_by == "price_asc":
            fetch_query = fetch_query.order_by(Product.price.asc())
        elif sort_by == "price_desc":
            fetch_query = fetch_query.order_by(Product.price.desc())
        elif sort_by == "name_asc":
            fetch_query = fetch_query.order_by(Product.name.asc())
        elif sort_by == "name_desc":
            fetch_query = fetch_query.order_by(Product.name.desc())
        else: # newest
            fetch_query = fetch_query.order_by(Product.created_at.desc())

        # Apply pagination
        fetch_query = fetch_query.offset(skip).limit(limit)
        
        result = await db.execute(fetch_query)
        products = result.scalars().all()
        
        return list(products), total_count
