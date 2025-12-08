# ============================================
# BotFactory AI - Payments API
# ============================================

from datetime import datetime, timedelta
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_current_user, DBSession, CurrentUser
from src.core.config import settings
from src.core.logging import payment_logger
from src.models.user import User, SubscriptionType
from src.models.payment import Payment, PaymentProvider, PaymentStatus, PaymentType
from src.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentList,
    PaymentListResponse,
    PaymentInitResponse,
    SubscriptionPlan,
    SubscriptionPlans,
    SubscriptionStatus,
)
from src.schemas.common import SuccessResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


# Subscription plan details
SUBSCRIPTION_PLANS = [
    SubscriptionPlan(
        type=SubscriptionType.FREE,
        name="Bepul",
        price_monthly=0,
        bot_limit=1,
        message_limit=100,
        features=[
            "1 ta bot",
            "100 ta xabar/oy",
            "Telegram integratsiyasi",
            "Asosiy AI javoblar",
        ],
    ),
    SubscriptionPlan(
        type=SubscriptionType.STARTER,
        name="Starter",
        price_monthly=165_000,
        bot_limit=3,
        message_limit=1000,
        features=[
            "3 ta bot",
            "1,000 ta xabar/oy",
            "Telegram + WhatsApp",
            "Bilimlar bazasi",
            "Email qo'llab-quvvatlash",
        ],
    ),
    SubscriptionPlan(
        type=SubscriptionType.BASIC,
        name="Basic",
        price_monthly=290_000,
        bot_limit=10,
        message_limit=10000,
        features=[
            "10 ta bot",
            "10,000 ta xabar/oy",
            "Barcha platformalar",
            "Bilimlar bazasi + FAQ",
            "Tezkor qo'llab-quvvatlash",
            "Analitika",
        ],
    ),
    SubscriptionPlan(
        type=SubscriptionType.PREMIUM,
        name="Premium",
        price_monthly=590_000,
        bot_limit=50,
        message_limit=100000,
        features=[
            "50 ta bot",
            "100,000 ta xabar/oy",
            "Barcha platformalar",
            "Shaxsiy AI sozlamalari",
            "Prioritet qo'llab-quvvatlash",
            "API kirish",
            "Custom branding",
        ],
    ),
]


@router.get("/plans", response_model=SubscriptionPlans)
async def get_subscription_plans():
    """
    Mavjud obuna rejalarini olish.
    """
    return SubscriptionPlans(plans=SUBSCRIPTION_PLANS)


@router.get("/subscription", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Joriy obuna holatini olish.
    """
    # Count user's bots
    result = await db.execute(
        select(func.count()).select_from(
            select(1).where(1 == current_user.id)  # Placeholder
        )
    )
    bots_used = 0  # TODO: Implement actual count

    days_remaining = None
    if current_user.subscription_expires_at:
        delta = current_user.subscription_expires_at - datetime.utcnow()
        days_remaining = max(0, delta.days)

    return SubscriptionStatus(
        type=current_user.subscription_type,
        expires_at=current_user.subscription_expires_at,
        is_active=current_user.is_subscription_active,
        days_remaining=days_remaining,
        bot_limit=current_user.bot_limit,
        bots_used=bots_used,
        message_limit=current_user.message_limit,
        messages_used=current_user.messages_this_month,
    )


@router.post("/create", response_model=PaymentInitResponse)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Yangi to'lov yaratish.
    """
    # Get subscription price
    prices = {
        SubscriptionType.STARTER: settings.PRICE_STARTER,
        SubscriptionType.BASIC: settings.PRICE_BASIC,
        SubscriptionType.PREMIUM: settings.PRICE_PREMIUM,
    }

    if payment_data.subscription_type == SubscriptionType.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bepul obuna uchun to'lov kerak emas",
        )

    base_price = prices.get(payment_data.subscription_type)
    if not base_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Noto'g'ri obuna turi",
        )

    # Calculate total amount
    total_amount = base_price * payment_data.subscription_months

    # Create payment record
    transaction_id = str(uuid.uuid4())
    payment = Payment(
        user_id=current_user.id,
        provider=payment_data.provider,
        payment_type=PaymentType.SUBSCRIPTION,
        amount=total_amount,
        status=PaymentStatus.PENDING,
        transaction_id=transaction_id,
        subscription_type=payment_data.subscription_type.value,
        subscription_months=payment_data.subscription_months,
        return_url=payment_data.return_url,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    # TODO: Generate actual payment URL based on provider
    payment_url = f"https://checkout.{payment_data.provider.value}.uz/pay/{transaction_id}"

    payment_logger.info(
        f"Payment created: {payment.id} for user {current_user.username}, "
        f"amount: {total_amount / 100} UZS"
    )

    return PaymentInitResponse(
        payment_id=payment.id,
        payment_url=payment_url,
        expires_at=payment.expires_at,
    )


@router.get("", response_model=PaymentListResponse)
async def list_payments(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[PaymentStatus] = None,
):
    """
    Foydalanuvchi to'lovlari ro'yxati.
    """
    query = select(Payment).where(Payment.user_id == current_user.id)

    if status_filter:
        query = query.where(Payment.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Payment.created_at.desc())

    result = await db.execute(query)
    payments = result.scalars().all()

    return PaymentListResponse(
        items=[PaymentList.model_validate(p) for p in payments],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    To'lov ma'lumotlarini olish.
    """
    result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
        )
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="To'lov topilmadi",
        )

    return payment


@router.post("/{payment_id}/cancel", response_model=SuccessResponse)
async def cancel_payment(
    payment_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    To'lovni bekor qilish.
    """
    result = await db.execute(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
        )
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="To'lov topilmadi",
        )

    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faqat kutilayotgan to'lovlarni bekor qilish mumkin",
        )

    payment.status = PaymentStatus.CANCELLED
    payment.updated_at = datetime.utcnow()
    await db.commit()

    payment_logger.info(f"Payment cancelled: {payment_id} by user {current_user.username}")

    return SuccessResponse(message="To'lov bekor qilindi")
