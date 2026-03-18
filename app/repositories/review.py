from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Tuple, Optional
from app.repositories.base import BaseRepository
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate

class ReviewRepository(BaseRepository[Review, ReviewCreate, ReviewUpdate]):
    
    async def get_product_reviews(
        self, db: AsyncSession, product_id: str, skip: int = 0, limit: int = 50, only_approved: bool = True
    ) -> List[Review]:
        query = select(Review).where(Review.product_id == product_id)
        if only_approved:
            query = query.where(Review.is_approved == True)
        query = query.order_by(Review.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_product_review_stats(self, db: AsyncSession, product_id: str) -> Tuple[int, float]:
        """Returns (count, average_rating) for a product's approved reviews"""
        query = select(
            func.count(Review.id),
            func.avg(Review.rating)
        ).where(
            Review.product_id == product_id,
            Review.is_approved == True
        )
        result = await db.execute(query)
        row = result.first()
        if row:
            count = row[0] or 0
            avg_rating = float(row[1]) if row[1] is not None else 0.0
            return count, avg_rating
        return 0, 0.0
