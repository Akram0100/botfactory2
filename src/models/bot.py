# ============================================
# BotFactory AI - Bot Model
# ============================================

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Any
import enum

from sqlalchemy import String, Boolean, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.knowledge import KnowledgeBase
    from src.models.chat import ChatHistory


class BotPlatform(str, enum.Enum):
    """Supported bot platforms."""
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"


class BotStatus(str, enum.Enum):
    """Bot status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"


class BotLanguage(str, enum.Enum):
    """Supported languages."""
    UZ = "uz"  # O'zbekcha
    RU = "ru"  # Ruscha
    EN = "en"  # Inglizcha


class Bot(Base):
    """Bot model representing a user's chatbot."""

    __tablename__ = "bots"

    # Owner relationship
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Platform configuration
    platform: Mapped[BotPlatform] = mapped_column(
        Enum(BotPlatform), nullable=False
    )
    token: Mapped[str] = mapped_column(String(500), nullable=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500))
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(100))

    # AI Configuration
    language: Mapped[BotLanguage] = mapped_column(
        Enum(BotLanguage), default=BotLanguage.UZ
    )
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(default=1000)

    # Behavior settings (stored as JSON)
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Status
    status: Mapped[BotStatus] = mapped_column(
        Enum(BotStatus), default=BotStatus.PENDING
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Statistics
    total_messages: Mapped[int] = mapped_column(default=0)
    total_users: Mapped[int] = mapped_column(default=0)
    last_message_at: Mapped[Optional[datetime]] = mapped_column()

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="bots")
    knowledge_items: Mapped[List["KnowledgeBase"]] = relationship(
        back_populates="bot",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    chat_history: Mapped[List["ChatHistory"]] = relationship(
        back_populates="bot",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    @property
    def default_settings(self) -> dict[str, Any]:
        """Default bot settings."""
        return {
            "greeting_message": "Salom! Men sizga qanday yordam bera olaman?",
            "fallback_message": "Kechirasiz, bu savolga javob topa olmadim.",
            "typing_delay": 1.0,
            "enable_typing_indicator": True,
            "enable_read_receipts": True,
            "max_context_messages": 10,
            "enable_audio_messages": True,
        }

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting with fallback to default."""
        defaults = self.default_settings
        return self.settings.get(key, defaults.get(key, default))

    def __repr__(self) -> str:
        return f"<Bot(id={self.id}, name='{self.name}', platform={self.platform.value})>"
