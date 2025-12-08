# ============================================
# BotFactory AI - User Schemas
# ============================================

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.models.user import SubscriptionType


# ===========================================
# Request Schemas
# ===========================================

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("username")
    @classmethod
    def username_lowercase(cls, v: str) -> str:
        return v.lower()


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    telegram_id: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordReset(BaseModel):
    """Schema for password reset."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ===========================================
# Response Schemas
# ===========================================

class UserBase(BaseModel):
    """Base user schema."""
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    model_config = {"from_attributes": True}


class UserResponse(UserBase):
    """User response schema."""
    subscription_type: SubscriptionType
    subscription_expires_at: Optional[datetime] = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    # Computed fields
    bot_limit: int
    message_limit: int
    is_subscription_active: bool
    can_send_message: bool


class UserPublic(BaseModel):
    """Public user profile (visible to others)."""
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    model_config = {"from_attributes": True}


class UserList(BaseModel):
    """Paginated user list."""
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


# ===========================================
# Token Schemas
# ===========================================

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request."""
    refresh_token: str


class TokenPayload(BaseModel):
    """Token payload."""
    sub: str
    exp: datetime
    type: str
