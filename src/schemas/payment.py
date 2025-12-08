# ============================================
# BotFactory AI - Payment Schemas
# ============================================

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field

from src.models.payment import PaymentProvider, PaymentStatus, PaymentType
from src.models.user import SubscriptionType


# ===========================================
# Request Schemas
# ===========================================

class PaymentCreate(BaseModel):
    """Schema for creating a payment."""
    subscription_type: SubscriptionType
    subscription_months: int = Field(default=1, ge=1, le=12)
    provider: PaymentProvider
    return_url: Optional[str] = Field(None, max_length=500)


class PaymentWebhook(BaseModel):
    """Generic payment webhook schema."""
    provider: PaymentProvider
    raw_data: dict[str, Any]


# ===========================================
# Response Schemas
# ===========================================

class PaymentBase(BaseModel):
    """Base payment schema."""
    id: int
    provider: PaymentProvider
    payment_type: PaymentType
    amount: int  # in tiyin
    currency: str
    status: PaymentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentResponse(PaymentBase):
    """Full payment response schema."""
    user_id: int
    transaction_id: Optional[str] = None
    subscription_type: Optional[str] = None
    subscription_months: int
    payment_url: Optional[str] = None
    paid_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def amount_uzs(self) -> float:
        """Amount in UZS."""
        return self.amount / 100


class PaymentList(BaseModel):
    """Payment list item."""
    id: int
    provider: PaymentProvider
    amount: int
    status: PaymentStatus
    subscription_type: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentListResponse(BaseModel):
    """Paginated payment list."""
    items: List[PaymentList]
    total: int
    page: int
    size: int


class PaymentInitResponse(BaseModel):
    """Payment initialization response."""
    payment_id: int
    payment_url: str
    expires_at: datetime


# ===========================================
# Subscription Schemas
# ===========================================

class SubscriptionPlan(BaseModel):
    """Subscription plan details."""
    type: SubscriptionType
    name: str
    price_monthly: int  # UZS
    bot_limit: int
    message_limit: int
    features: List[str]


class SubscriptionPlans(BaseModel):
    """All subscription plans."""
    plans: List[SubscriptionPlan]


class SubscriptionStatus(BaseModel):
    """Current subscription status."""
    type: SubscriptionType
    expires_at: Optional[datetime] = None
    is_active: bool
    days_remaining: Optional[int] = None
    bot_limit: int
    bots_used: int
    message_limit: int
    messages_used: int


# ===========================================
# PayMe Specific Schemas
# ===========================================

class PaymeWebhook(BaseModel):
    """PayMe webhook schema."""
    method: str
    params: dict[str, Any]


class PaymeCheckPerform(BaseModel):
    """PayMe CheckPerformTransaction."""
    amount: int
    account: dict[str, str]


class PaymeCreateTransaction(BaseModel):
    """PayMe CreateTransaction."""
    id: str
    time: int
    amount: int
    account: dict[str, str]


# ===========================================
# Click Specific Schemas
# ===========================================

class ClickPrepare(BaseModel):
    """Click Prepare request."""
    click_trans_id: str
    service_id: str
    merchant_trans_id: str
    amount: float
    action: int
    sign_time: str
    sign_string: str


class ClickComplete(BaseModel):
    """Click Complete request."""
    click_trans_id: str
    service_id: str
    merchant_trans_id: str
    merchant_prepare_id: str
    amount: float
    action: int
    sign_time: str
    sign_string: str
    error: int


# ===========================================
# Uzum Specific Schemas
# ===========================================

class UzumWebhook(BaseModel):
    """Uzum webhook schema."""
    transaction_id: str
    amount: int
    status: str
    merchant_trans_id: str
    sign: str
