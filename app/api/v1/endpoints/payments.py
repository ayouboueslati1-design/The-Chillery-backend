from typing import Optional

from authorizenet import apicontractsv1 as ApiContracts
from authorizenet import apicontrollers as ApiControllers
from authorizenet.apicontrollersbase import APIOperationBase
from authorizenet.constants import constants as ANetConstants
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import OrderCreateRequest, OrderItemCreate, ShippingAddress
from app.services.order import OrderService

router = APIRouter()


class OpaqueDataIn(BaseModel):
    dataDescriptor: str
    dataValue: str


class ChargeRequest(BaseModel):
    amount: float = Field(..., gt=0)
    opaque_data: OpaqueDataIn
    items: list[OrderItemCreate]
    shipping_address: ShippingAddress
    shipping_method: Optional[str] = None
    guest_email: Optional[str] = None
    guest_name: Optional[str] = None


class ChargeResponse(BaseModel):
    success: bool
    transaction_id: str
    auth_code: Optional[str] = None
    response_code: str
    order_number: str


class RefundRequest(BaseModel):
    original_transaction_id: str
    amount: float = Field(..., gt=0)


class RefundResponse(BaseModel):
    success: bool
    transaction_id: str


class WebhookEvent(BaseModel):
    eventType: str
    payload: dict


def _merchant_auth() -> ApiContracts.merchantAuthenticationType:
    if not settings.ANET_API_LOGIN_ID or not settings.ANET_TRANSACTION_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authorize.Net is not configured.",
        )

    auth = ApiContracts.merchantAuthenticationType()
    auth.name = settings.ANET_API_LOGIN_ID
    auth.transactionKey = settings.ANET_TRANSACTION_KEY
    return auth


def _configure_environment() -> None:
    endpoint = (
        ANetConstants.PRODUCTION
        if settings.NODE_ENV.lower() == "production"
        else ANetConstants.SANDBOX
    )
    APIOperationBase.setenvironment(endpoint)


def _get_attr(obj, *attrs):
    current = obj
    for attr in attrs:
        if current is None:
            return None
        current = getattr(current, attr, None)
        if isinstance(current, list):
            current = current[0] if current else None
    return current


def _safe_ref_id(user_id: str) -> str:
    """Authorize.Net refId has a strict max length; keep a compact stable value."""
    compact = str(user_id).replace("-", "")
    return f"u{compact}"[:20]


@router.post("/charge", response_model=ChargeResponse, status_code=status.HTTP_201_CREATED)
async def charge_card(
    body: ChargeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ChargeResponse:
    _configure_environment()

    opaque_data = ApiContracts.opaqueDataType()
    opaque_data.dataDescriptor = body.opaque_data.dataDescriptor
    opaque_data.dataValue = body.opaque_data.dataValue

    payment_type = ApiContracts.paymentType()
    payment_type.opaqueData = opaque_data

    transaction_request = ApiContracts.transactionRequestType()
    transaction_request.transactionType = "authCaptureTransaction"
    transaction_request.amount = round(body.amount, 2)
    transaction_request.payment = payment_type

    create_request = ApiContracts.createTransactionRequest()
    create_request.merchantAuthentication = _merchant_auth()
    create_request.transactionRequest = transaction_request
    create_request.refId = _safe_ref_id(str(current_user.id)) if current_user else "guest"

    controller = ApiControllers.createTransactionController(create_request)
    controller.execute()
    response = controller.getresponse()

    result_code = str(_get_attr(response, "messages", "resultCode") or "")
    response_code = str(_get_attr(response, "transactionResponse", "responseCode") or "")
    trans_id = _get_attr(response, "transactionResponse", "transId")
    auth_code = _get_attr(response, "transactionResponse", "authCode")

    if result_code == "Ok" and response_code == "1" and trans_id:
        order_service = OrderService(db)
        try:
            order = await order_service.create_paid_order(
                payload=OrderCreateRequest(
                    transaction_id=str(trans_id),
                    auth_code=str(auth_code) if auth_code else None,
                    amount_total=body.amount,
                    items=body.items,
                    shipping_address=body.shipping_address,
                    shipping_method=body.shipping_method,
                    guest_email=body.guest_email,
                    guest_name=body.guest_name,
                ),
                current_user=current_user,
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment captured but order creation failed for transaction {trans_id}: {exc}",
            )

        return ChargeResponse(
            success=True,
            transaction_id=str(trans_id),
            auth_code=str(auth_code) if auth_code else None,
            response_code=response_code,
            order_number=order.order_number,
        )

    error_text = _get_attr(response, "transactionResponse", "errors", "error", "errorText")
    if not error_text:
        error_text = _get_attr(response, "messages", "message", "text")

    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail=str(error_text or "Transaction failed"),
    )


@router.post("/refund", response_model=RefundResponse)
async def refund_transaction(body: RefundRequest, current_user: User = Depends(get_current_user)) -> RefundResponse:
    _configure_environment()

    transaction_request = ApiContracts.transactionRequestType()
    transaction_request.transactionType = "refundTransaction"
    transaction_request.amount = round(body.amount, 2)
    transaction_request.refTransId = body.original_transaction_id

    create_request = ApiContracts.createTransactionRequest()
    create_request.merchantAuthentication = _merchant_auth()
    create_request.transactionRequest = transaction_request
    create_request.refId = _safe_ref_id(str(current_user.id))

    controller = ApiControllers.createTransactionController(create_request)
    controller.execute()
    response = controller.getresponse()

    result_code = str(_get_attr(response, "messages", "resultCode") or "")
    response_code = str(_get_attr(response, "transactionResponse", "responseCode") or "")
    trans_id = _get_attr(response, "transactionResponse", "transId")

    if result_code == "Ok" and response_code == "1" and trans_id:
        return RefundResponse(success=True, transaction_id=str(trans_id))

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Refund failed",
    )


@router.post("/webhook/authorizenet")
async def authorizenet_webhook(event: WebhookEvent):
    event_type = event.eventType
    payload = event.payload or {}
    transaction_id = payload.get("id")

    if event_type == "net.authorize.payment.authcapture.created":
        # TODO: mark order confirmed by transaction_id
        return {"ok": True, "event": event_type, "transaction_id": transaction_id}

    if event_type == "net.authorize.payment.void.created":
        # TODO: mark order cancelled by transaction_id
        return {"ok": True, "event": event_type, "transaction_id": transaction_id}

    if event_type == "net.authorize.payment.refund.created":
        # TODO: mark order refunded by transaction_id
        return {"ok": True, "event": event_type, "transaction_id": transaction_id}

    return {"ok": True, "event": event_type}
