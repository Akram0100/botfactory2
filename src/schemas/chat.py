# ============================================
# BotFactory AI - Chat Schemas
# ============================================

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field

from src.models.chat import MessageType, MessageRole


# ===========================================
# Request Schemas
# ===========================================

class ChatMessage(BaseModel):
    """Incoming chat message."""
    content: str = Field(..., min_length=1, max_length=4000)
    message_type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None


class ChatFeedback(BaseModel):
    """Chat message feedback."""
    message_id: int
    score: int = Field(..., ge=1, le=5)
    text: Optional[str] = Field(None, max_length=500)


# ===========================================
# Response Schemas
# ===========================================

class ChatMessageBase(BaseModel):
    """Base chat message schema."""
    id: int
    role: MessageRole
    message_type: MessageType
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageResponse(ChatMessageBase):
    """Full chat message response."""
    bot_id: int
    platform_user_id: str
    platform_username: Optional[str] = None
    media_url: Optional[str] = None
    tokens_used: int
    response_time_ms: int
    feedback_score: Optional[int] = None


class ChatHistoryItem(BaseModel):
    """Chat history list item."""
    id: int
    role: MessageRole
    content: str
    message_type: MessageType
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    """Chat history response."""
    items: List[ChatHistoryItem]
    total: int
    has_more: bool


class ChatSession(BaseModel):
    """Chat session summary."""
    session_id: str
    platform_user_id: str
    platform_username: Optional[str] = None
    message_count: int
    first_message_at: datetime
    last_message_at: datetime


class ChatSessionList(BaseModel):
    """Chat sessions list."""
    items: List[ChatSession]
    total: int
    page: int
    size: int


# ===========================================
# Bot Platform Message Schemas
# ===========================================

class BotMessage(BaseModel):
    """Internal bot message representation."""
    sender_id: str
    text: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BotResponse(BaseModel):
    """Bot response to send."""
    text: str
    buttons: List[dict[str, Any]] = Field(default_factory=list)
    image_url: Optional[str] = None
    audio_url: Optional[str] = None


# ===========================================
# Analytics Schemas
# ===========================================

class ChatAnalytics(BaseModel):
    """Chat analytics."""
    total_messages: int
    total_users: int
    messages_by_day: dict[str, int]
    average_response_time_ms: float
    most_active_hours: List[int]
    satisfaction_score: Optional[float] = None


class UserActivity(BaseModel):
    """User activity summary."""
    platform_user_id: str
    platform_username: Optional[str] = None
    total_messages: int
    first_seen: datetime
    last_seen: datetime
    average_satisfaction: Optional[float] = None
