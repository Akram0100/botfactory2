# ============================================
# BotFactory AI - Authentication API
# ============================================

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_current_user, DBSession, CurrentUser
from src.core.security import (
    get_password_hash,
    verify_password,
    create_token_pair,
    verify_token,
)
from src.core.logging import api_logger
from src.models.user import User
from src.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    PasswordChange,
    Token,
    TokenRefresh,
)
from src.schemas.common import SuccessResponse, MessageResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: DBSession,
):
    """
    Yangi foydalanuvchi ro'yxatdan o'tkazish.
    
    - **email**: Elektron pochta manzili (unikal)
    - **username**: Foydalanuvchi nomi (3-64 belgi, faqat a-z, 0-9, _)
    - **password**: Parol (kamida 8 belgi)
    """
    # Check if email or username already exists
    result = await db.execute(
        select(User).where(
            or_(
                User.email == user_data.email,
                User.username == user_data.username.lower(),
            )
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu email allaqachon ro'yxatdan o'tgan",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu username allaqachon band",
        )

    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username.lower(),
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)

    api_logger.info(f"New user registered: {user.username} ({user.email})")
    
    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: DBSession,
):
    """
    Tizimga kirish va JWT token olish.
    
    - **email**: Elektron pochta manzili
    - **password**: Parol
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Noto'g'ri email yoki parol",
        )

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Noto'g'ri email yoki parol",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Foydalanuvchi bloklangan",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Create tokens
    token_pair = create_token_pair(user.id)

    api_logger.info(f"User logged in: {user.username}")

    return Token(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: DBSession,
):
    """
    Refresh token yordamida yangi access token olish.
    """
    user_id = verify_token(token_data.refresh_token, token_type="refresh")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Noto'g'ri yoki muddati o'tgan refresh token",
        )

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi topilmadi yoki bloklangan",
        )

    # Create new tokens
    token_pair = create_token_pair(user.id)

    return Token(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """
    Joriy foydalanuvchi ma'lumotlarini olish.
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Profil ma'lumotlarini yangilash.
    """
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)

    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Parolni o'zgartirish.
    """
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Joriy parol noto'g'ri",
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    await db.commit()

    api_logger.info(f"Password changed for user: {current_user.username}")

    return SuccessResponse(message="Parol muvaffaqiyatli o'zgartirildi")


@router.post("/logout", response_model=SuccessResponse)
async def logout(current_user: CurrentUser):
    """
    Tizimdan chiqish.
    
    Note: JWT tokens are stateless. This endpoint is for client-side cleanup.
    For production, implement token blacklisting with Redis.
    """
    api_logger.info(f"User logged out: {current_user.username}")
    return SuccessResponse(message="Muvaffaqiyatli chiqdingiz")
