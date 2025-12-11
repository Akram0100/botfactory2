# ============================================
# BotFactory AI - Bots API
# ============================================

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import (
    get_db, get_current_user, get_user_bot,
    DBSession, CurrentUser,
)
from src.core.logging import api_logger
from src.models.user import User
from src.models.bot import Bot, BotPlatform, BotStatus
from src.schemas.bot import (
    BotCreate,
    BotUpdate,
    BotTokenUpdate,
    BotResponse,
    BotList,
    BotListResponse,
    BotStats,
    BotValidation,
)
from src.schemas.common import SuccessResponse, DeleteResponse

router = APIRouter(prefix="/bots", tags=["Bots"])


@router.get("", response_model=BotListResponse)
async def list_bots(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    platform: Optional[BotPlatform] = None,
    is_active: Optional[bool] = None,
):
    """
    Foydalanuvchi botlari ro'yxatini olish.
    
    - **page**: Sahifa raqami
    - **size**: Sahifadagi elementlar soni
    - **platform**: Platform bo'yicha filter (telegram/whatsapp/instagram)
    - **is_active**: Faollik bo'yicha filter
    """
    # Build query
    query = select(Bot).where(Bot.user_id == current_user.id)
    
    if platform:
        query = query.where(Bot.platform == platform)
    if is_active is not None:
        query = query.where(Bot.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Bot.created_at.desc())

    result = await db.execute(query)
    bots = result.scalars().all()

    return BotListResponse(
        items=[BotList.model_validate(bot) for bot in bots],
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Yangi bot yaratish.
    
    - **name**: Bot nomi
    - **platform**: Platforma (telegram/whatsapp/instagram)
    - **token**: Bot tokeni
    - **language**: Til (uz/ru/en)
    """
    # Check bot limit
    result = await db.execute(
        select(func.count()).where(Bot.user_id == current_user.id)
    )
    current_bot_count = result.scalar() or 0

    if current_bot_count >= current_user.bot_limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Bot limiti ({current_user.bot_limit}) to'lgan. Obunani yangilang.",
        )

    # Check if token already exists
    result = await db.execute(
        select(Bot).where(Bot.token == bot_data.token)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu token allaqachon ishlatilgan",
        )

    # Create bot
    bot = Bot(
        user_id=current_user.id,
        name=bot_data.name,
        description=bot_data.description,
        platform=bot_data.platform,
        token=bot_data.token,
        language=bot_data.language,
        system_prompt=bot_data.system_prompt,
        temperature=bot_data.temperature,
        max_tokens=bot_data.max_tokens,
        settings=bot_data.settings,
        status=BotStatus.PENDING,
    )

    db.add(bot)
    await db.commit()
    await db.refresh(bot)

    api_logger.info(f"Bot created: {bot.name} (ID: {bot.id}) by user {current_user.username}")

    return bot


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Bot ma'lumotlarini olish.
    """
    bot = await get_user_bot(bot_id, current_user, db)
    return bot


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int,
    bot_data: BotUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Bot ma'lumotlarini yangilash.
    """
    bot = await get_user_bot(bot_id, current_user, db)
    
    update_data = bot_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(bot, field, value)

    bot.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(bot)

    api_logger.info(f"Bot updated: {bot.name} (ID: {bot.id})")

    return bot


@router.delete("/{bot_id}", response_model=DeleteResponse)
async def delete_bot(
    bot_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Botni o'chirish.
    """
    bot = await get_user_bot(bot_id, current_user, db)
    
    await db.delete(bot)
    await db.commit()

    api_logger.info(f"Bot deleted: {bot.name} (ID: {bot.id}) by user {current_user.username}")

    return DeleteResponse(id=bot_id)


@router.post("/{bot_id}/activate", response_model=BotResponse)
async def activate_bot(
    bot_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Botni faollashtirish.
    """
    import os
    from src.services.bots.telegram import TelegramBot
    
    bot = await get_user_bot(bot_id, current_user, db)
    
    # Set up webhook for Telegram bots
    if bot.platform == BotPlatform.TELEGRAM:
        telegram_bot = TelegramBot(
            bot_id=bot.id,
            token=bot.token,
            config=bot.settings or {},
        )
        
        # Validate token first
        try:
            is_valid = await telegram_bot.validate_token()
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Telegram token noto'g'ri",
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token tekshirishda xatolik: {str(e)}",
            )
        
        # Set up webhook
        base_url = os.environ.get("WEBHOOK_BASE_URL", os.environ.get("REPLIT_DEV_DOMAIN", ""))
        if base_url and not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        
        if base_url:
            webhook_url = f"{base_url}/api/v1/webhooks/telegram/{bot.token}"
            try:
                await telegram_bot.setup_webhook(webhook_url)
                bot.webhook_url = webhook_url
            except Exception as e:
                api_logger.warning(f"Failed to set webhook: {e}")
    
    bot.is_active = True
    bot.status = BotStatus.ACTIVE
    bot.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(bot)

    api_logger.info(f"Bot activated: {bot.name} (ID: {bot.id})")

    return bot


@router.post("/{bot_id}/deactivate", response_model=BotResponse)
async def deactivate_bot(
    bot_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Botni to'xtatish.
    """
    bot = await get_user_bot(bot_id, current_user, db)
    
    bot.is_active = False
    bot.status = BotStatus.INACTIVE
    bot.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(bot)

    api_logger.info(f"Bot deactivated: {bot.name} (ID: {bot.id})")

    return bot


@router.patch("/{bot_id}/token", response_model=SuccessResponse)
async def update_bot_token(
    bot_id: int,
    token_data: BotTokenUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Bot tokenini yangilash.
    """
    bot = await get_user_bot(bot_id, current_user, db)

    # Check if new token already exists
    result = await db.execute(
        select(Bot).where(Bot.token == token_data.token, Bot.id != bot_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu token allaqachon ishlatilgan",
        )

    bot.token = token_data.token
    bot.status = BotStatus.PENDING  # Need to re-validate
    bot.updated_at = datetime.utcnow()
    
    await db.commit()

    api_logger.info(f"Bot token updated: {bot.name} (ID: {bot.id})")

    return SuccessResponse(message="Token muvaffaqiyatli yangilandi")


@router.get("/{bot_id}/stats", response_model=BotStats)
async def get_bot_stats(
    bot_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Bot statistikasini olish.
    """
    bot = await get_user_bot(bot_id, current_user, db)

    # TODO: Calculate actual statistics from chat_history and knowledge_base
    return BotStats(
        total_messages=bot.total_messages,
        total_users=bot.total_users,
        messages_today=0,
        messages_this_week=0,
        messages_this_month=0,
        average_response_time_ms=0,
        knowledge_items_count=len(bot.knowledge_items) if bot.knowledge_items else 0,
    )


@router.post("/{bot_id}/validate", response_model=BotValidation)
async def validate_bot_token(
    bot_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Bot tokenini tekshirish va platformadan bot ma'lumotlarini olish.
    """
    bot = await get_user_bot(bot_id, current_user, db)

    # TODO: Implement actual validation based on platform
    # For now, return mock validation
    return BotValidation(
        valid=True,
        bot_username=f"bot_{bot.id}",
        bot_name=bot.name,
    )
