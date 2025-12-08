# ============================================
# BotFactory AI - Chat History Model
# ============================================

from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any
import enum

from sqlalchemy import String, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.bot import Bot


class MessageType(str, enum.Enum):
    """Message types."""
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"


class MessageRole(str, enum.Enum):
    """Message role."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatHistory(Base):
    """Chat history model for storing conversations."""

    __tablename__ = "chat_history"

    # Bot relationship
    bot_id: Mapped[int] = mapped_column(
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User identification (platform-specific)
    platform_user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    platform_username: Mapped[Optional[str]] = mapped_column(String(100))

    # Session tracking
    session_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    # Message content
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType), default=MessageType.TEXT
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # For non-text messages
    media_url: Mapped[Optional[str]] = mapped_column(String(500))
    media_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # AI response metadata
    ai_model: Mapped[Optional[str]] = mapped_column(String(100))
    tokens_used: Mapped[int] = mapped_column(default=0)
    response_time_ms: Mapped[int] = mapped_column(default=0)

    # Context used for response
    context_ids: Mapped[list[int]] = mapped_column(JSON, default=list)  # KnowledgeBase IDs used

    # Platform message IDs
    platform_message_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Feedback
    feedback_score: Mapped[Optional[int]] = mapped_column()  # 1-5 rating
    feedback_text: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    bot: Mapped["Bot"] = relationship(back_populates="chat_history")

    def __repr__(self) -> str:
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<ChatHistory(id={self.id}, role={self.role.value}, content='{content_preview}')>"
