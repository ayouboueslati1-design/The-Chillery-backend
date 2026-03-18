from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List, Optional
from slugify import slugify
from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryTreeResponse
from uuid import UUID

class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CategoryRepository(Category)
        
    async def create_category(self, data: CategoryCreate) -> Category:
        slug = slugify(data.name)
        existing = await self.repo.get_by_slug(self.db, slug)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists.")
        
        # We manually build the dict from CategoryCreate but override the generated dict to inject slug
        obj_in = data.model_dump()
        obj_in["slug"] = slug
        
        new_category = Category(**obj_in)
        self.db.add(new_category)
        await self.db.commit()
        await self.db.refresh(new_category)
        return new_category

    async def get_categories(self, skip: int = 0, limit: int = 100) -> List[Category]:
        return await self.repo.get_active_categories(self.db, skip=skip, limit=limit)
        
    async def get_category_by_id(self, category_id: str) -> Optional[Category]:
        return await self.repo.get(self.db, category_id)

    async def get_category_by_slug(self, slug: str) -> Optional[Category]:
        cat = await self.repo.get_by_slug(self.db, slug)
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
        return cat

    async def update_category(self, category_id: str, data: CategoryUpdate) -> Category:
        cat = await self.repo.get(self.db, category_id)
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
            
        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"]:
            new_slug = slugify(update_data["name"])
            if new_slug != cat.slug:
                existing = await self.repo.get_by_slug(self.db, new_slug)
                if existing:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New category name already exists.")
                update_data["slug"] = new_slug
                
        return await self.repo.update(self.db, db_obj=cat, obj_in=update_data)

    async def delete_category(self, category_id: str):
        cat = await self.repo.get(self.db, category_id)
        if not cat:     
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
            
        # Optional: check if there are nested categories or products attached, for safety
        await self.repo.remove(self.db, id=category_id)
