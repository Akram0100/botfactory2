# ============================================
# BotFactory AI - User Model
# ============================================

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import enum

from sqlalchemy import String, Boolean, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.bot import Bot
    from src.models.payment import Payment


class SubscriptionType(str, enum.Enum):
    """Subscription types."""
    FREE = "free"
    STARTER = "starter"
    BASIC = "basic"
    PREMIUM = "premium"


# Bot limits per subscription
BOT_LIMITS = {
    SubscriptionType.FREE: 1,
    SubscriptionType.STARTER: 3,
    SubscriptionType.BASIC: 10,
    SubscriptionType.PREMIUM: 50,
}

# Message limits per month
MESSAGE_LIMITS = {
    SubscriptionType.FREE: 100,
    SubscriptionType.STARTER: 1000,
    SubscriptionType.BASIC: 10000,
    SubscriptionType.PREMIUM: 100000,
}


class User(Base):
    """User model for authentication and profile."""

    __tablename__ = "users"

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    telegram_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)

    # Subscription
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        Enum(SubscriptionType), default=SubscriptionType.FREE, nullable=False
    )
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column()
    messages_this_month: Mapped[int] = mapped_column(default=0)
    messages_reset_at: Mapped[Optional[datetime]] = mapped_column()

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    # Last activity
    last_login_at: Mapped[Optional[datetime]] = mapped_column()
    last_active_at: Mapped[Optional[datetime]] = mapped_column()

    # Relationships
    bots: Mapped[List["Bot"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    payments: Mapped[List["Payment"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    @property
    def bot_limit(self) -> int:
        """Get bot limit for current subscription."""
        return BOT_LIMITS.get(self.subscription_type, 1)

    @property
    def message_limit(self) -> int:
        """Get monthly message limit for current subscription."""
        return MESSAGE_LIMITS.get(self.subscription_type, 100)

    @property
    def is_subscription_active(self) -> bool:
        """Check if subscription is still active."""
        if self.subscription_type == SubscriptionType.FREE:
            return True
        if self.subscription_expires_at is None:
            return False
        return self.subscription_expires_at > datetime.utcnow()

    @property
    def can_send_message(self) -> bool:
        """Check if user can send more messages this month."""
        return self.messages_this_month < self.message_limit

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
