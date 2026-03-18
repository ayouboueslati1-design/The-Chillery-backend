from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import List

from app.models.cart import CartItem
from app.models.product import Product
from app.models.product_image import ProductImage
from app.schemas.cart import CartItemCreate, CartItemUpdate


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cart(self, user_id: str) -> List[CartItem]:
        result = await self.db.execute(
            select(CartItem)
            .options(
                selectinload(CartItem.product).selectinload(Product.images),
            )
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.created_at)
        )
        return list(result.scalars().all())

    async def add_item(self, user_id: str, data: CartItemCreate) -> CartItem:
        product = await self.db.get(Product, data.product_id)
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        existing_result = await self.db.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == data.product_id,
                CartItem.selected_color == data.selected_color,
                CartItem.selected_size == data.selected_size,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            existing.quantity += data.quantity
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        item = CartItem(
            user_id=user_id,
            product_id=data.product_id,
            quantity=data.quantity,
            selected_color=data.selected_color,
            selected_size=data.selected_size,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_item(
        self, user_id: str, item_id: str, data: CartItemUpdate
    ) -> CartItem | None:
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.id == item_id, CartItem.user_id == user_id
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found."
            )
        if data.quantity <= 0:
            await self.db.delete(item)
            await self.db.commit()
            return None
        item.quantity = data.quantity
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def remove_item(self, user_id: str, item_id: str) -> None:
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.id == item_id, CartItem.user_id == user_id
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found."
            )
        await self.db.delete(item)
        await self.db.commit()

    async def clear_cart(self, user_id: str) -> None:
        result = await self.db.execute(
            select(CartItem).where(CartItem.user_id == user_id)
        )
        for item in result.scalars().all():
            await self.db.delete(item)
        await self.db.commit()

    async def merge_guest_cart(
        self, user_id: str, guest_items: List[CartItemCreate]
    ) -> None:
        """Merge guest cart items into the authenticated user's backend cart."""
        for item_data in guest_items:
            try:
                await self.add_item(user_id, item_data)
            except HTTPException:
                pass  # skip items for deleted/inactive products
