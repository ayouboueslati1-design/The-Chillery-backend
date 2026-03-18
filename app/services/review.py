from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
from app.models.review import Review
from app.models.product import Product
from app.repositories.review import ReviewRepository
from app.repositories.product import ProductRepository
from app.schemas.review import ReviewCreate, ReviewApprove


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.review_repo = ReviewRepository(Review)
        self.product_repo = ProductRepository(Product)

    async def create_review(self, product_id: str, data: ReviewCreate, user_id: Optional[str] = None) -> Review:
        # Check if product exists
        prod = await self.product_repo.get(self.db, product_id)
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        
        if not user_id and not data.author_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must provide an author name if not logged in.")

        obj_in = data.model_dump()
        obj_in["product_id"] = product_id
        if user_id:
            obj_in["user_id"] = user_id
            
        # Could also set verified_purchase if user_id is provided and order history confirms it
        
        new_review = Review(**obj_in)
        self.db.add(new_review)
        await self.db.commit()
        await self.db.refresh(new_review)
        return new_review

    async def get_reviews_for_product(self, product_id: str, skip: int = 0, limit: int = 50, only_approved: bool = True) -> List[Review]:
        return await self.review_repo.get_product_reviews(self.db, product_id=product_id, skip=skip, limit=limit, only_approved=only_approved)

    async def approve_review(self, review_id: str, data: ReviewApprove) -> Review:
        review = await self.review_repo.get(self.db, review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
            
        review.is_approved = data.is_approved
        if data.response:
            review.response = data.response
            review.response_at = _utcnow()
            
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def mark_helpful(self, review_id: str) -> Review:
        review = await self.review_repo.get(self.db, review_id)
        if not review:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
        
        review.helpful_count += 1
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review
