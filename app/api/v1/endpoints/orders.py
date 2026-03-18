from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import (
    OrderCreateRequest,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdateRequest,
)
from app.services.order import OrderService

router = APIRouter()


@router.post("/create", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order_after_payment(
    payload: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(deps.get_optional_current_user),
):
    service = OrderService(db)
    return await service.create_paid_order(payload=payload, current_user=current_user)


@router.get("/my-orders", response_model=list[OrderResponse])
async def get_my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    service = OrderService(db)
    return await service.get_my_orders(str(current_user.id))


@router.get("/confirmation/{order_number}", response_model=OrderResponse)
async def get_confirmation_order(
    order_number: str,
    guest_email: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    return await service.get_public_order(order_number=order_number, guest_email=guest_email)


@router.get("/admin", response_model=OrderListResponse)
async def list_orders_admin(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    q: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    _ = current_user
    service = OrderService(db)
    orders, total = await service.list_orders_admin(
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        query=q,
    )
    return {
        "items": orders,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.patch("/admin/{order_number}/status", response_model=OrderResponse)
async def update_order_status(
    order_number: str,
    payload: OrderStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    _ = current_user
    service = OrderService(db)
    return await service.update_order_status(order_number=order_number, payload=payload)


@router.get("/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    service = OrderService(db)
    return await service.get_order_for_user(order_number=order_number, user=current_user)
