from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartItemResponse, CartResponse
from app.services.cart import CartService

router = APIRouter()


@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get the current user's cart."""
    service = CartService(db)
    items = await service.get_cart(str(current_user.id))
    total = sum(float(item.product.price) * item.quantity for item in items)
    count = sum(item.quantity for item in items)
    return {"items": items, "total": total, "count": count}


@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    data: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Add an item to the cart."""
    service = CartService(db)
    return await service.add_item(str(current_user.id), data)


@router.put("/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: str,
    data: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Update cart item quantity. Quantity <= 0 removes the item."""
    service = CartService(db)
    result = await service.update_item(str(current_user.id), item_id, data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Item removed because quantity was set to 0.",
        )
    return result


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Remove an item from the cart."""
    service = CartService(db)
    await service.remove_item(str(current_user.id), item_id)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Clear all items from the cart."""
    service = CartService(db)
    await service.clear_cart(str(current_user.id))


@router.post("/merge", status_code=status.HTTP_204_NO_CONTENT)
async def merge_guest_cart(
    items: List[CartItemCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Merge a guest cart into the authenticated user's cart. Call after login."""
    service = CartService(db)
    await service.merge_guest_cart(str(current_user.id), items)
