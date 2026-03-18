from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import CartItem
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.order import OrderCreateRequest, OrderStatusUpdateRequest


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_order_number(self) -> str:
        year = _utcnow().year
        prefix = f"CHI-{year}-"

        result = await self.db.execute(
            select(Order.order_number)
            .where(Order.order_number.like(f"{prefix}%"))
            .order_by(Order.order_number.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        last_seq = int(str(latest).split("-")[-1]) if latest else 0
        return f"{prefix}{last_seq + 1:05d}"

    async def create_paid_order(
        self,
        payload: OrderCreateRequest,
        current_user: Optional[User],
    ) -> Order:
        if not payload.items:
            raise HTTPException(status_code=400, detail="Order must include at least one item")

        if not current_user and not payload.guest_email:
            raise HTTPException(status_code=400, detail="guest_email is required for guest checkout")

        order_number = await self._generate_order_number()

        order = Order(
            order_number=order_number,
            user_id=str(current_user.id) if current_user else None,
            guest_email=payload.guest_email,
            guest_name=payload.guest_name,
            status=OrderStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            transaction_id=payload.transaction_id,
            auth_code=payload.auth_code,
            amount_total=payload.amount_total,
            shipping_address=payload.shipping_address.model_dump(),
            shipping_method=payload.shipping_method,
        )
        self.db.add(order)
        await self.db.flush()

        for item in payload.items:
            product_result = await self.db.execute(
                select(Product)
                .options(selectinload(Product.images))
                .where(Product.id == item.product_id)
            )
            product = product_result.scalar_one_or_none()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {item.product_id} not found",
                )

            image_url = product.images[0].url if product.images else None
            subtotal = float(item.unit_price) * int(item.quantity)

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                product_image=image_url,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                subtotal=float(subtotal),
            )
            self.db.add(order_item)

        # Logged-in checkouts consume the server-side cart.
        if current_user:
            await self.db.execute(
                delete(CartItem).where(CartItem.user_id == str(current_user.id))
            )

        await self.db.commit()

        refreshed = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.user))
            .where(Order.id == order.id)
        )
        return refreshed.scalar_one()

    async def get_my_orders(self, user_id: str) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_order_for_user(self, order_number: str, user: User) -> Order:
        stmt = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.user))
            .where(Order.order_number == order_number)
        )

        if user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
            stmt = stmt.where(Order.user_id == str(user.id))

        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    async def get_public_order(self, order_number: str, guest_email: Optional[str]) -> Order:
        if not guest_email:
            raise HTTPException(status_code=400, detail="guest_email is required")

        stmt = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.user))
            .where(Order.order_number == order_number)
        )
        stmt = stmt.where(Order.guest_email == guest_email, Order.user_id.is_(None))

        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    async def list_orders_admin(
        self,
        skip: int = 0,
        limit: int = 10,
        status_filter: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        query: Optional[str] = None,
    ) -> tuple[list[Order], int]:
        filters = []
        if status_filter:
            filters.append(Order.status == status_filter)
        if date_from:
            filters.append(Order.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            filters.append(Order.created_at <= datetime.combine(date_to, datetime.max.time()))
        if query:
            pattern = f"%{query}%"
            filters.append(
                or_(
                    Order.order_number.ilike(pattern),
                    Order.guest_email.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )

        total_stmt = select(func.count(Order.id)).select_from(Order).outerjoin(User)
        if filters:
            total_stmt = total_stmt.where(*filters)
        total = int((await self.db.execute(total_stmt)).scalar_one() or 0)

        stmt = (
            select(Order)
            .outerjoin(User)
            .options(selectinload(Order.items), selectinload(Order.user))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if filters:
            stmt = stmt.where(*filters)

        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def update_order_status(
        self, order_number: str, payload: OrderStatusUpdateRequest
    ) -> Order:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.user))
            .where(Order.order_number == order_number)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        current_status = str(order.status)
        next_status = payload.status

        allowed_transitions = {
            "pending": {"confirmed", "cancelled"},
            "confirmed": {"processing", "cancelled", "refunded"},
            "processing": {"shipped", "cancelled", "refunded"},
            "shipped": {"delivered", "refunded"},
            "delivered": {"refunded"},
            "cancelled": set(),
            "refunded": set(),
        }

        if next_status != current_status and next_status not in allowed_transitions.get(current_status, set()):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition: {current_status} -> {next_status}",
            )

        order.status = next_status
        if payload.tracking_number:
            order.tracking_number = payload.tracking_number
        if next_status == "refunded":
            order.payment_status = PaymentStatus.REFUNDED

        order.updated_at = _utcnow()
        await self.db.commit()
        await self.db.refresh(order)
        return order
