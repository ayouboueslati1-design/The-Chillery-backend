from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

class CategoryRepository(BaseRepository[Category, CategoryCreate, CategoryUpdate]):
    
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Category]:
        query = select(Category).where(Category.slug == slug)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_active_categories(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Category]:
        query = select(Category).where(Category.is_active == True).order_by(Category.sort_order).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
        
    async def get_category_tree(self, db: AsyncSession) -> List[Category]:
        # Simple tree query. For deep trees CTEs are better, but this handles simple top-level requests
        query = select(Category).where(Category.parent_id == None, Category.is_active == True).order_by(Category.sort_order)
        result = await db.execute(query)
        return result.scalars().all()
