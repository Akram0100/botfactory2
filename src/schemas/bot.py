# ============================================
# BotFactory AI - Bot Schemas
# ============================================

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field

from src.models.bot import BotPlatform, BotStatus, BotLanguage


# ===========================================
# Request Schemas
# ===========================================

class BotCreate(BaseModel):
    """Schema for creating a new bot."""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    platform: BotPlatform
    token: str = Field(..., min_length=10)
    language: BotLanguage = BotLanguage.UZ
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=1000, ge=100, le=4000)
    settings: dict[str, Any] = Field(default_factory=dict)


class BotUpdate(BaseModel):
    """Schema for updating a bot."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=500)
    language: Optional[BotLanguage] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=100, le=4000)
    settings: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class BotTokenUpdate(BaseModel):
    """Schema for updating bot token."""
    token: str = Field(..., min_length=10)


# ===========================================
# Response Schemas
# ===========================================

class BotBase(BaseModel):
    """Base bot schema."""
    id: int
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    platform: BotPlatform
    language: BotLanguage
    status: BotStatus
    is_active: bool

    model_config = {"from_attributes": True}


class BotResponse(BotBase):
    """Full bot response schema."""
    user_id: int
    webhook_url: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float
    max_tokens: int
    settings: dict[str, Any]
    total_messages: int
    total_users: int
    last_message_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BotList(BaseModel):
    """Bot list item (simplified)."""
    id: int
    name: str
    platform: BotPlatform
    status: BotStatus
    is_active: bool
    total_messages: int
    total_users: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BotListResponse(BaseModel):
    """Paginated bot list response."""
    items: List[BotList]
    total: int
    page: int
    size: int


class BotStats(BaseModel):
    """Bot statistics."""
    total_messages: int
    total_users: int
    messages_today: int
    messages_this_week: int
    messages_this_month: int
    average_response_time_ms: float
    knowledge_items_count: int


# ===========================================
# Webhook Schemas
# ===========================================

class WebhookSetup(BaseModel):
    """Webhook setup response."""
    webhook_url: str
    webhook_secret: str
    instructions: str


class BotValidation(BaseModel):
    """Bot token validation result."""
    valid: bool
    bot_username: Optional[str] = None
    bot_name: Optional[str] = None
    error: Optional[str] = None
