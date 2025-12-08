# ============================================
# BotFactory AI - Admin API
# ============================================

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_current_admin_user, DBSession, AdminUser
from src.core.logging import api_logger
from src.models.user import User, SubscriptionType
from src.models.bot import Bot
from src.models.payment import Payment, PaymentStatus
from src.schemas.user import UserResponse, UserList
from src.schemas.common import SuccessResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def get_admin_stats(
    admin_user: AdminUser,
    db: DBSession,
):
    """
    Platform statistikasi (faqat adminlar uchun).
    """
    # Total users
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    
    # Active users (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.last_active_at > thirty_days_ago)
    )).scalar() or 0

    # Users by subscription
    subscription_counts = {}
    for sub_type in SubscriptionType:
        count = (await db.execute(
            select(func.count(User.id)).where(User.subscription_type == sub_type)
        )).scalar() or 0
        subscription_counts[sub_type.value] = count

    # Total bots
    total_bots = (await db.execute(select(func.count(Bot.id)))).scalar() or 0
    active_bots = (await db.execute(
        select(func.count(Bot.id)).where(Bot.is_active == True)
    )).scalar() or 0

    # Revenue this month
    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    monthly_revenue = (await db.execute(
        select(func.sum(Payment.amount)).where(
            and_(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.paid_at >= first_of_month,
            )
        )
    )).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "active_last_30_days": active_users,
            "by_subscription": subscription_counts,
        },
        "bots": {
            "total": total_bots,
            "active": active_bots,
        },
        "revenue": {
            "this_month_uzs": monthly_revenue / 100,
        },
    }


@router.get("/users", response_model=UserList)
async def list_all_users(
    admin_user: AdminUser,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    subscription: Optional[SubscriptionType] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
):
    """
    Barcha foydalanuvchilar ro'yxati (faqat adminlar uchun).
    """
    query = select(User)

    if subscription:
        query = query.where(User.subscription_type == subscription)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        query = query.where(
            User.email.ilike(f"%{search}%") | 
            User.username.ilike(f"%{search}%")
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Calculate pages
    pages = (total + size - 1) // size if size > 0 else 0

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    return UserList(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.post("/users/{user_id}/ban", response_model=SuccessResponse)
async def ban_user(
    user_id: int,
    admin_user: AdminUser,
    db: DBSession,
):
    """
    Foydalanuvchini bloklash.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi",
        )

    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin foydalanuvchini bloklash mumkin emas",
        )

    user.is_banned = True
    user.is_active = False
    user.updated_at = datetime.utcnow()
    await db.commit()

    api_logger.warning(f"User banned: {user.username} by admin {admin_user.username}")

    return SuccessResponse(message=f"Foydalanuvchi {user.username} bloklandi")


@router.post("/users/{user_id}/unban", response_model=SuccessResponse)
async def unban_user(
    user_id: int,
    admin_user: AdminUser,
    db: DBSession,
):
    """
    Foydalanuvchi blokini ochish.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi",
        )

    user.is_banned = False
    user.is_active = True
    user.updated_at = datetime.utcnow()
    await db.commit()

    api_logger.info(f"User unbanned: {user.username} by admin {admin_user.username}")

    return SuccessResponse(message=f"Foydalanuvchi {user.username} bloki ochildi")


@router.post("/users/{user_id}/set-subscription", response_model=SuccessResponse)
async def set_user_subscription(
    user_id: int,
    subscription_type: SubscriptionType,
    admin_user: AdminUser,
    db: DBSession,
    months: int = Query(default=1, ge=1, le=12),
):
    """
    Foydalanuvchi obunasini sozlash (admin).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi",
        )

    user.subscription_type = subscription_type
    if subscription_type != SubscriptionType.FREE:
        user.subscription_expires_at = datetime.utcnow() + timedelta(days=30 * months)
    else:
        user.subscription_expires_at = None
    user.updated_at = datetime.utcnow()
    await db.commit()

    api_logger.info(
        f"Subscription set: {user.username} -> {subscription_type.value} "
        f"by admin {admin_user.username}"
    )

    return SuccessResponse(
        message=f"Obuna {subscription_type.value} ga o'zgartirildi ({months} oy)"
    )
