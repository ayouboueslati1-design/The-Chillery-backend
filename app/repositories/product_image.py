from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.repositories.base import BaseRepository
from app.models.product_image import ProductImage
from app.schemas.product_image import ProductImageCreate

# Notice the Update schema defaults to ProductImageCreate here, or you could create a specific Update schema
class ProductImageRepository(BaseRepository[ProductImage, ProductImageCreate, ProductImageCreate]):
    
    async def get_by_product(self, db: AsyncSession, product_id: str) -> List[ProductImage]:
        query = select(ProductImage).where(ProductImage.product_id == product_id).order_by(ProductImage.sort_order)
        result = await db.execute(query)
        return result.scalars().all()
