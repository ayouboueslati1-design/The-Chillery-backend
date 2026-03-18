from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import limiter
from app.api.v1 import router as v1_router

logger = logging.getLogger(__name__)


async def create_super_admin() -> None:
    """Create the default super admin account if it doesn't already exist."""
    from app.db.session import AsyncSessionLocal
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == settings.SUPER_ADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info("Super admin already exists: %s", settings.SUPER_ADMIN_EMAIL)
            return

        super_admin = User(
            email=settings.SUPER_ADMIN_EMAIL,
            password_hash=get_password_hash(settings.SUPER_ADMIN_PASSWORD),
            first_name="Super",
            last_name="Admin",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db.add(super_admin)
        await db.commit()
        logger.info("Super admin created: %s", settings.SUPER_ADMIN_EMAIL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: run startup tasks then yield."""
    setup_logging()
    await create_super_admin()
    yield  # app runs here


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Serve uploaded images as static files
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to The Chillery API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(v1_router, prefix="/api/v1")
