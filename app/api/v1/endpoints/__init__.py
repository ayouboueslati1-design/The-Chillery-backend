from fastapi import APIRouter
from app.api.v1.endpoints import auth, categories, cart, orders, payments, products, reviews, upload

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(categories.router, prefix="/categories", tags=["categories"])
router.include_router(cart.router, prefix="/cart", tags=["cart"])
router.include_router(orders.router, prefix="/orders", tags=["orders"])
router.include_router(payments.router, prefix="/payments", tags=["payments"])
router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
router.include_router(upload.router, prefix="/upload", tags=["upload"])