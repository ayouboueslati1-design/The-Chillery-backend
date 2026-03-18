from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category import CategoryService

router = APIRouter()

@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """Retrieve all active categories."""
    service = CategoryService(db)
    # Returning tree view for simplicity, or just list based on service
    # In a full app, this might build a nested tree structure
    cats = await service.get_categories(skip=skip, limit=limit)
    return cats

@router.get("/{slug}", response_model=CategoryResponse)
async def get_category(
    slug: str, db: AsyncSession = Depends(get_db)
):
    """Retrieve category by slug."""
    service = CategoryService(db)
    return await service.get_category_by_slug(slug)

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_admin)
):
    """Create a new category. Admin only."""
    service = CategoryService(db)
    return await service.create_category(data)

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str, 
    data: CategoryUpdate, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_admin)
):
    """Update a category. Admin only."""
    service = CategoryService(db)
    return await service.update_category(category_id, data)

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str, 
    db: AsyncSession = Depends(get_db),
    current_admin = Depends(deps.get_current_admin)
):
    """Delete a category. Admin only."""
    service = CategoryService(db)
    await service.delete_category(category_id)
