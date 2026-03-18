from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import ReviewResponse, ReviewApprove
from app.services.review import ReviewService

router = APIRouter()


@router.put("/{review_id}/approve", response_model=ReviewResponse)
async def approve_review(
    review_id: str,
    data: ReviewApprove,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(deps.get_current_admin),
):
    """Approve or reject a review, optionally add an admin response. Admin only."""
    service = ReviewService(db)
    return await service.approve_review(review_id, data)


@router.post("/{review_id}/helpful", response_model=ReviewResponse)
async def mark_review_helpful(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(deps.get_current_user),
):
    """Increment the helpful_count for a review. Requires authentication."""
    service = ReviewService(db)
    return await service.mark_helpful(review_id)
