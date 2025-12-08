# ============================================
# BotFactory AI - Application Configuration
# ============================================

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "BotFactory AI"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/botfactory"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    @property
    def async_database_url(self) -> str:
        """Convert DATABASE_URL to async format."""
        url = self.DATABASE_URL
        # Convert postgresql:// to postgresql+asyncpg://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Convert postgres:// to postgresql+asyncpg://
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        # Handle sslmode parameter for asyncpg
        if "sslmode=" in url:
            url = url.replace("sslmode=", "ssl=")
        return url

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Settings
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google Gemini AI
    GOOGLE_API_KEY: str = ""
    AI_MODEL: str = "gemini-2.0-flash-exp"
    AI_MAX_TOKENS: int = 2000
    AI_TEMPERATURE: float = 0.7

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # WhatsApp (Meta)
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "botfactory_verify"

    # Instagram
    INSTAGRAM_ACCESS_TOKEN: str = ""

    # PayMe
    PAYME_MERCHANT_ID: str = ""
    PAYME_SECRET_KEY: str = ""

    # Click
    CLICK_MERCHANT_ID: str = ""
    CLICK_SERVICE_ID: str = ""
    CLICK_SECRET_KEY: str = ""

    # Uzum
    UZUM_MERCHANT_ID: str = ""
    UZUM_SECRET_KEY: str = ""

    # Subscription Prices (UZS - in tiyin, 1 UZS = 100 tiyin)
    PRICE_STARTER: int = 165_000_00  # 165,000 UZS
    PRICE_BASIC: int = 290_000_00     # 290,000 UZS
    PRICE_PREMIUM: int = 590_000_00   # 590,000 UZS

    # Webhook
    WEBHOOK_BASE_URL: str = ""

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    @property
    def subscription_prices(self) -> dict[str, int]:
        """Get subscription prices dictionary."""
        return {
            "starter": self.PRICE_STARTER,
            "basic": self.PRICE_BASIC,
            "premium": self.PRICE_PREMIUM,
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()
