from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # App
    APP_NAME: str = "The Chillery API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    NODE_ENV: str = "development"
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS – comma-separated list of allowed origins
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Authorize.Net (PaymentCloud)
    ANET_API_LOGIN_ID: str = ""
    ANET_TRANSACTION_KEY: str = ""
    ANET_PUBLIC_CLIENT_KEY: str = ""

    # Super Admin (must be set in .env)
    SUPER_ADMIN_EMAIL: str
    SUPER_ADMIN_PASSWORD: str

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

settings = Settings()