# ============================================
# BotFactory AI - Payment Model
# ============================================

from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any
import enum

from sqlalchemy import String, Enum, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.user import User


class PaymentProvider(str, enum.Enum):
    """Payment providers."""
    PAYME = "payme"
    CLICK = "click"
    UZUM = "uzum"


class PaymentStatus(str, enum.Enum):
    """Payment status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentType(str, enum.Enum):
    """Payment type."""
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    REFUND = "refund"


class Payment(Base):
    """Payment model for tracking transactions."""

    __tablename__ = "payments"

    # User relationship
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Payment info
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider), nullable=False
    )
    payment_type: Mapped[PaymentType] = mapped_column(
        Enum(PaymentType), default=PaymentType.SUBSCRIPTION
    )

    # Amount (in tiyin, 1 UZS = 100 tiyin)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="UZS")

    # Status
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING
    )

    # Transaction IDs
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    provider_transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # For subscription payments
    subscription_type: Mapped[Optional[str]] = mapped_column(String(50))
    subscription_months: Mapped[int] = mapped_column(default=1)

    # Provider-specific data
    provider_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # URLs
    payment_url: Mapped[Optional[str]] = mapped_column(String(500))
    return_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Timestamps
    paid_at: Mapped[Optional[datetime]] = mapped_column()
    expires_at: Mapped[Optional[datetime]] = mapped_column()

    # Error handling
    error_code: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(String(500))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="payments")

    @property
    def amount_uzs(self) -> float:
        """Get amount in UZS (from tiyin)."""
        return self.amount / 100

    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == PaymentStatus.COMPLETED

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount_uzs} UZS, status={self.status.value})>"
