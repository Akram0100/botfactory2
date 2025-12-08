# ============================================
# BotFactory AI - API Dependencies
# ============================================

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import verify_token
from src.core.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    NotFoundError,
    AuthorizationError,
    SubscriptionRequiredError,
)
from src.db.session import get_db
from src.models.user import User, SubscriptionType
from src.models.bot import Bot

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current authenticated user from JWT token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token kerak",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user_id = verify_token(token, token_type="access")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Noto'g'ri yoki muddati o'tgan token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi topilmadi",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Foydalanuvchi bloklangan",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Foydalanuvchi bloklangan",
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin huquqi kerak",
        )
    return current_user


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email tasdiqlanishi kerak",
        )
    return current_user


def require_subscription(min_plan: SubscriptionType = SubscriptionType.STARTER):
    """Dependency factory for subscription requirements."""
    async def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        plan_order = {
            SubscriptionType.FREE: 0,
            SubscriptionType.STARTER: 1,
            SubscriptionType.BASIC: 2,
            SubscriptionType.PREMIUM: 3,
        }
        
        if not current_user.is_subscription_active:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Obuna muddati tugagan",
            )
        
        user_plan_level = plan_order.get(current_user.subscription_type, 0)
        required_level = plan_order.get(min_plan, 0)
        
        if user_plan_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Bu funksiya uchun {min_plan.value} obunasi kerak",
            )
        
        return current_user
    
    return dependency


async def get_user_bot(
    bot_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Bot:
    """Get a bot that belongs to the current user."""
    result = await db.execute(
        select(Bot).where(Bot.id == bot_id, Bot.user_id == current_user.id)
    )
    bot = result.scalar_one_or_none()

    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot topilmadi",
        )

    return bot


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]
VerifiedUser = Annotated[User, Depends(get_current_verified_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
